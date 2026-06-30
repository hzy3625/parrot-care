package com.parrotcare.mobile;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.parrotcare.mobile.audio.AudioRecorder;
import com.parrotcare.mobile.data.LocalStore;

import java.io.File;
import java.io.IOException;

public final class MainActivity extends Activity {
    private static final int RECORD_AUDIO_REQUEST = 100;

    private final AudioRecorder audioRecorder = new AudioRecorder();
    private LocalStore localStore;
    private TextView statusText;
    private Button recordButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        localStore = new LocalStore(getApplicationContext());
        statusText = findViewById(R.id.status_text);
        recordButton = findViewById(R.id.record_button);
        recordButton.setOnClickListener(view -> toggleRecording());
    }

    private void toggleRecording() {
        if (audioRecorder.isRecording()) {
            saveRecording();
            return;
        }
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, RECORD_AUDIO_REQUEST);
            return;
        }
        startRecording();
    }

    private void startRecording() {
        File audioDirectory = new File(getFilesDir(), "audio");
        if (!audioDirectory.exists() && !audioDirectory.mkdirs()) {
            showFailure();
            return;
        }
        File target = new File(audioDirectory, "recording-" + System.currentTimeMillis() + ".m4a");
        try {
            audioRecorder.start(target);
            statusText.setText(R.string.stop);
            recordButton.setText(R.string.stop);
        } catch (IOException | RuntimeException error) {
            showFailure();
        }
    }

    private void saveRecording() {
        File recording = audioRecorder.stop();
        if (recording == null) {
            showFailure();
            return;
        }
        localStore.saveRecording(recording);
        statusText.setText(R.string.saved);
        recordButton.setText(R.string.record);
        Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show();
    }

    private void showFailure() {
        statusText.setText(R.string.record_failed);
        recordButton.setText(R.string.record);
        Toast.makeText(this, R.string.record_failed, Toast.LENGTH_SHORT).show();
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != RECORD_AUDIO_REQUEST) {
            return;
        }
        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            startRecording();
        } else {
            statusText.setText(R.string.permission_denied);
        }
    }

    @Override
    protected void onStop() {
        if (audioRecorder.isRecording()) {
            audioRecorder.cancel();
            statusText.setText(R.string.ready);
            recordButton.setText(R.string.record);
        }
        super.onStop();
    }

    @Override
    protected void onDestroy() {
        localStore.close();
        super.onDestroy();
    }
}
