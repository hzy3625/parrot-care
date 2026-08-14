package com.parrotcare.mobile.audio;

import android.media.AudioFormat;
import android.media.MediaCodec;
import android.media.MediaExtractor;
import android.media.MediaFormat;

import java.io.File;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

public final class AudioFeatureExtractor {
    private static final long CODEC_TIMEOUT_US = 10_000L;
    private static final long MAX_ANALYSIS_US = 180_000_000L;
    private static final long MAX_WALL_TIME_MS = 30_000L;
    private static final double ACTIVE_THRESHOLD = 0.02d;

    public AudioFeatures extract(File file) throws IOException {
        if (file == null || !file.isFile() || file.length() == 0L) {
            throw new IOException("音频文件不可用");
        }

        MediaExtractor extractor = new MediaExtractor();
        MediaCodec codec = null;
        try {
            extractor.setDataSource(file.getAbsolutePath());
            MediaFormat inputFormat = selectAudioTrack(extractor);
            String mime = inputFormat.getString(MediaFormat.KEY_MIME);
            if (mime == null) throw new IOException("无法识别音频格式");

            codec = MediaCodec.createDecoderByType(mime);
            codec.configure(inputFormat, null, null, 0);
            codec.start();
            return decode(codec, extractor);
        } catch (RuntimeException error) {
            throw new IOException("音频解析失败", error);
        } finally {
            if (codec != null) {
                try {
                    codec.stop();
                } catch (RuntimeException ignored) {
                    // Decoder may already be stopped after a codec failure.
                }
                codec.release();
            }
            extractor.release();
        }
    }

    private MediaFormat selectAudioTrack(MediaExtractor extractor) throws IOException {
        for (int index = 0; index < extractor.getTrackCount(); index++) {
            MediaFormat format = extractor.getTrackFormat(index);
            String mime = format.getString(MediaFormat.KEY_MIME);
            if (mime != null && mime.startsWith("audio/")) {
                extractor.selectTrack(index);
                return format;
            }
        }
        throw new IOException("文件中没有音频轨道");
    }

    private AudioFeatures decode(MediaCodec codec, MediaExtractor extractor) throws IOException {
        MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();
        Accumulator accumulator = new Accumulator();
        boolean inputFinished = false;
        boolean outputFinished = false;
        int pcmEncoding = AudioFormat.ENCODING_PCM_16BIT;
        long deadline = System.currentTimeMillis() + MAX_WALL_TIME_MS;

        while (!outputFinished) {
            if (System.currentTimeMillis() > deadline) throw new IOException("音频分析超时");
            if (!inputFinished) {
                int inputIndex = codec.dequeueInputBuffer(CODEC_TIMEOUT_US);
                if (inputIndex >= 0) {
                    ByteBuffer input = codec.getInputBuffer(inputIndex);
                    if (input == null) throw new IOException("无法读取解码输入");
                    int size = extractor.readSampleData(input, 0);
                    long presentationUs = extractor.getSampleTime();
                    if (size < 0 || presentationUs > MAX_ANALYSIS_US) {
                        codec.queueInputBuffer(inputIndex, 0, 0, Math.max(0L, presentationUs), MediaCodec.BUFFER_FLAG_END_OF_STREAM);
                        inputFinished = true;
                    } else {
                        codec.queueInputBuffer(inputIndex, 0, size, presentationUs, 0);
                        extractor.advance();
                    }
                }
            }

            int outputIndex = codec.dequeueOutputBuffer(info, CODEC_TIMEOUT_US);
            if (outputIndex == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED) {
                MediaFormat outputFormat = codec.getOutputFormat();
                if (outputFormat.containsKey(MediaFormat.KEY_PCM_ENCODING)) {
                    pcmEncoding = outputFormat.getInteger(MediaFormat.KEY_PCM_ENCODING);
                }
            } else if (outputIndex >= 0) {
                ByteBuffer output = codec.getOutputBuffer(outputIndex);
                if (output != null && info.size > 0) {
                    output.position(info.offset);
                    output.limit(info.offset + info.size);
                    accumulator.accept(output.slice().order(ByteOrder.LITTLE_ENDIAN), pcmEncoding);
                }
                outputFinished = (info.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0;
                codec.releaseOutputBuffer(outputIndex, false);
            }
        }

        if (accumulator.samples == 0L) throw new IOException("音频没有可分析的声音数据");
        return accumulator.result();
    }

    private static final class Accumulator {
        long samples;
        long activeSamples;
        double squareSum;
        double peak;

        void accept(ByteBuffer buffer, int encoding) {
            if (encoding == AudioFormat.ENCODING_PCM_FLOAT) {
                while (buffer.remaining() >= 4) acceptSample(Math.abs(buffer.getFloat()));
                return;
            }
            if (encoding == AudioFormat.ENCODING_PCM_8BIT) {
                while (buffer.hasRemaining()) acceptSample(Math.abs(((buffer.get() & 0xff) - 128) / 128.0d));
                return;
            }
            while (buffer.remaining() >= 2) acceptSample(Math.abs(buffer.getShort() / 32768.0d));
        }

        void acceptSample(double sample) {
            if (!Double.isFinite(sample)) return;
            double safe = Math.min(1.0d, sample);
            samples++;
            squareSum += safe * safe;
            if (safe > peak) peak = safe;
            if (safe >= ACTIVE_THRESHOLD) activeSamples++;
        }

        AudioFeatures result() {
            double rms = Math.sqrt(squareSum / samples);
            return new AudioFeatures(
                toDb(rms),
                toDb(peak),
                activeSamples / (double) samples,
                samples
            );
        }

        private double toDb(double amplitude) {
            return 20.0d * Math.log10(Math.max(amplitude, 0.000001d));
        }
    }
}
