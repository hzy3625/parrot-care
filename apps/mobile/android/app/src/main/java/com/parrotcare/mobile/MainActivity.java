package com.parrotcare.mobile;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import com.parrotcare.mobile.audio.AudioPlayer;
import com.parrotcare.mobile.audio.AudioRecorder;
import com.parrotcare.mobile.audio.AudioFeatureExtractor;
import com.parrotcare.mobile.audio.AudioFeatures;
import com.parrotcare.mobile.audio.BaselineComparison;
import com.parrotcare.mobile.data.AudioFileStore;
import com.parrotcare.mobile.data.BackupStore;
import com.parrotcare.mobile.data.LocalStore;
import com.parrotcare.mobile.data.LocalStore.ParrotEvent;
import com.parrotcare.mobile.data.LocalStore.ParrotProfile;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final int RECORD_AUDIO_REQUEST = 100;
    private static final int IMPORT_AUDIO_REQUEST = 101;
    private static final int IMPORT_BACKUP_REQUEST = 102;
    private static final String PREFS = "parrotcare";
    private static final String PREF_CURRENT_PARROT = "current_parrot_id";
    private static final long MIN_AUDIO_BYTES = 1024L;
    private static final long MIN_AUDIO_DURATION_MS = 800L;
    private static final String ORIGIN_HOME = "home";
    private static final String ORIGIN_LIBRARY = "library";

    private enum Screen {
        HOME,
        PARROTS,
        EDIT_PARROT,
        RECORDING,
        SAVE_EVENT,
        POST_SAVE,
        LIBRARY,
        DETAIL,
        COMPARISON
    }

    private static final Choice[] CATEGORIES = new Choice[]{
        new Choice("normal_chirp", "正常鸣叫"),
        new Choice("scream", "持续尖叫"),
        new Choice("night_fright", "夜间惊飞"),
        new Choice("plucking", "啄羽行为"),
        new Choice("silence", "异常安静"),
        new Choice("unclassified", "待确认录音")
    };
    private static final Choice[] STATUSES = new Choice[]{
        new Choice("pending", "待处理"),
        new Choice("reviewing", "观察中"),
        new Choice("resolved", "已处理"),
        new Choice("false_positive", "已排除")
    };
    private static final Choice[] PURPOSES = new Choice[]{
        new Choice("baseline", "日常基线"),
        new Choice("abnormal", "异常声音"),
        new Choice("manual", "无音频备注")
    };

    private final AudioRecorder recorder = new AudioRecorder();
    private final AudioPlayer player = new AudioPlayer();
    private final AudioFeatureExtractor featureExtractor = new AudioFeatureExtractor();
    private LocalStore store;
    private AudioFileStore files;
    private BackupStore backupStore;
    private SharedPreferences preferences;
    private ScrollView currentScrollView;
    private File pendingAudio;
    private String pendingRecordingPurpose = "abnormal";
    private long recordingStartedAt;
    private final Handler uiHandler = new Handler(Looper.getMainLooper());
    private TextView recordingTimerText;
    private final Runnable recordingTimer = new Runnable() {
        @Override
        public void run() {
            if (!recorder.isRecording() || recordingTimerText == null) {
                return;
            }
            long duration = System.currentTimeMillis() - recordingStartedAt;
            recordingTimerText.setText("已录制：" + formatDuration(duration));
            uiHandler.postDelayed(this, 500L);
        }
    };
    private String filterParrot = "all";
    private String filterCategory = "all";
    private String filterPurpose = "all";
    private String filterStatus = "all";
    private boolean libraryFiltersVisible = false;
    private Screen currentScreen = Screen.HOME;
    private String detailOrigin = ORIGIN_HOME;
    private String comparisonEventId;
    private String postSaveEventId;
    private String postSavePurpose = "abnormal";
    private boolean recordingInterrupted;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        store = new LocalStore(getApplicationContext());
        files = new AudioFileStore(getApplicationContext());
        backupStore = new BackupStore(getApplicationContext(), store, files);
        preferences = getSharedPreferences(PREFS, MODE_PRIVATE);
        ensureCurrentParrot();
        showHome();
    }

    @Override
    public void onBackPressed() {
        if (currentScreen == Screen.HOME) {
            super.onBackPressed();
            return;
        }
        navigateBack();
    }

    private void navigateBack() {
        switch (currentScreen) {
            case PARROTS:
            case LIBRARY:
            case POST_SAVE:
                showHome();
                break;
            case EDIT_PARROT:
                showParrots();
                break;
            case RECORDING:
                cancelRecording();
                break;
            case SAVE_EVENT:
                discardSaveDraft();
                showHome();
                break;
            case DETAIL:
                if (ORIGIN_LIBRARY.equals(detailOrigin)) {
                    showLibrary(0);
                } else {
                    showHome();
                }
                break;
            case COMPARISON:
                showDetail(store.getEvent(comparisonEventId), 0, detailOrigin);
                break;
            case HOME:
            default:
                finish();
                break;
        }
    }

    private void showHome() {
        player.stop();
        currentScreen = Screen.HOME;
        LinearLayout root = base("ParrotCare");
        root.addView(note("建议流程：给默认鹦鹉改名 → 录制 3 条日常基线 → 发现异常时录音 → 与基线对比。"));
        root.addView(body("本地优先的鹦鹉声音与健康记录。核心功能离线可用。"));

        String currentId = currentParrotId();
        ParrotProfile currentParrot = store.getParrot(currentId);
        int baselineCount = store.countBaselineAudioEvents(currentId);
        String parrotName = currentParrot == null ? "当前鹦鹉" : currentParrot.name;
        boolean needsBaseline = baselineCount < 3;

        LinearLayout baselinePanel = panel();
        baselinePanel.addView(section("日常声音基线"));
        if (needsBaseline) {
            baselinePanel.addView(note(
                parrotName + " 目前有 " + baselineCount + " / 3 条基线。先把基线录够，异常对比才更有参考价值。"
            ));
            baselinePanel.addView(body("尽量在相近距离、环境和手机位置录制。"));
            baselinePanel.addView(primaryButton("录制日常基线", v -> requestRecording("baseline")));
        } else {
            baselinePanel.addView(body(parrotName + " 已有 " + baselineCount + " 条基线，可用于声音变化对比。"));
            baselinePanel.addView(secondaryButton("再录一条基线", v -> requestRecording("baseline")));
        }

        LinearLayout capturePanel = panel();
        capturePanel.addView(section("捕获"));
        capturePanel.addView(body("录制或导入异常声音，也可写一条无音频备注。"));
        if (needsBaseline) {
            capturePanel.addView(secondaryButton("录制异常声音", v -> requestRecording("abnormal")));
        } else {
            capturePanel.addView(primaryButton("录制异常声音", v -> requestRecording("abnormal")));
        }
        capturePanel.addView(secondaryButton("导入音频", v -> pickAudio()));
        capturePanel.addView(secondaryButton("无音频备注", v -> showSaveEvent(null, "manual", 0L, "manual")));

        LinearLayout libraryPanel = panel();
        libraryPanel.addView(section("记录库"));
        libraryPanel.addView(body("查看最近条目，或打开完整列表。"));
        List<ParrotEvent> recent = store.recentEvents(5);
        if (recent.isEmpty()) {
            libraryPanel.addView(note("还没有条目。先录基线或异常声音。"));
        } else {
            for (ParrotEvent event : recent) {
                libraryPanel.addView(eventRow(event, ORIGIN_HOME));
            }
        }
        libraryPanel.addView(primaryButton("打开记录库", v -> showLibrary(0)));

        LinearLayout settingsPanel = panel();
        settingsPanel.addView(section("数据和设置"));
        settingsPanel.addView(body("管理鹦鹉档案，导出或导入备份。"));
        settingsPanel.addView(secondaryButton("鹦鹉档案", v -> showParrots()));
        settingsPanel.addView(secondaryButton("导出数据备份", v -> exportBackup()));
        settingsPanel.addView(secondaryButton("导入数据备份", v -> pickBackup()));

        if (needsBaseline) {
            root.addView(baselinePanel);
            root.addView(capturePanel);
        } else {
            root.addView(capturePanel);
            root.addView(baselinePanel);
        }
        root.addView(libraryPanel);
        root.addView(settingsPanel);

        setRoot(root, 0);
    }

    private void showParrots() {
        currentScreen = Screen.PARROTS;
        LinearLayout root = base("鹦鹉档案");
        List<ParrotProfile> parrots = store.listParrots();
        String currentId = currentParrotId();
        root.addView(note("当前鹦鹉会作为新条目的默认归属。"));
        for (ParrotProfile parrot : parrots) {
            LinearLayout panel = panel();
            panel.addView(section(parrot.name + (parrot.id.equals(currentId) ? "（当前）" : "")));
            panel.addView(body("品种：" + emptyLabel(parrot.species) + "\n生日/年龄：" + emptyLabel(parrot.birthday) + "\n备注：" + emptyLabel(parrot.note)));
            panel.addView(secondaryButton("设为当前鹦鹉", v -> {
                setCurrentParrot(parrot.id);
                showParrots();
            }));
            panel.addView(secondaryButton("编辑档案", v -> showEditParrot(parrot)));
            root.addView(panel);
        }
        root.addView(primaryButton("新增鹦鹉档案", v -> showEditParrot(null)));
        root.addView(secondaryButton("返回首页", v -> showHome()));
        setRoot(root, 0);
    }

    private void showEditParrot(ParrotProfile parrot) {
        currentScreen = Screen.EDIT_PARROT;
        LinearLayout root = base(parrot == null ? "新增鹦鹉" : "编辑鹦鹉");
        EditText name = input("名称", parrot == null ? "" : parrot.name);
        EditText species = input("品种，可选", parrot == null ? "" : parrot.species);
        EditText birthday = input("生日或年龄，可选", parrot == null ? "" : parrot.birthday);
        EditText note = input("备注，可选", parrot == null ? "" : parrot.note);
        root.addView(name);
        root.addView(species);
        root.addView(birthday);
        root.addView(note);
        root.addView(primaryButton("保存档案", v -> {
            String trimmedName = name.getText().toString().trim();
            if (trimmedName.length() == 0) {
                toast("名称不能为空");
                return;
            }
            if (parrot == null) {
                String id = store.saveParrot(trimmedName, species.getText().toString(), birthday.getText().toString(), note.getText().toString());
                setCurrentParrot(id);
            } else {
                parrot.name = trimmedName;
                parrot.species = species.getText().toString();
                parrot.birthday = birthday.getText().toString();
                parrot.note = note.getText().toString();
                store.updateParrot(parrot);
            }
            showParrots();
        }));
        root.addView(secondaryButton("返回档案", v -> navigateBack()));
        setRoot(root, 0);
    }

    private void requestRecording(String purpose) {
        pendingRecordingPurpose = "baseline".equals(purpose) ? "baseline" : "abnormal";
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, RECORD_AUDIO_REQUEST);
            return;
        }
        startRecording();
    }

    private void startRecording() {
        try {
            pendingAudio = files.newRecordingFile();
            recorder.start(pendingAudio);
            recordingStartedAt = System.currentTimeMillis();
            recordingInterrupted = false;
            showRecording();
        } catch (IOException | RuntimeException error) {
            files.deleteQuietly(pendingAudio);
            pendingAudio = null;
            toast("录音启动失败");
        }
    }

    private void showRecording() {
        currentScreen = Screen.RECORDING;
        LinearLayout root = base("正在录音");
        root.addView(note("录音中。停止后可试听，再决定是否保存。切到后台会中断录音。"));
        recordingTimerText = section("已录制：0分0秒");
        root.addView(recordingTimerText);
        root.addView(primaryButton("停止录音", v -> stopRecording()));
        root.addView(secondaryButton("取消录音", v -> cancelRecording()));
        setRoot(root, 0);
        uiHandler.removeCallbacks(recordingTimer);
        uiHandler.post(recordingTimer);
    }

    private void stopRecording() {
        uiHandler.removeCallbacks(recordingTimer);
        recordingTimerText = null;
        File audio = recorder.stop();
        long duration = System.currentTimeMillis() - recordingStartedAt;
        if (audio == null || !audio.exists() || audio.length() < MIN_AUDIO_BYTES || duration < MIN_AUDIO_DURATION_MS) {
            files.deleteQuietly(audio);
            pendingAudio = null;
            toast("录音太短或无效，未保存");
            showHome();
            return;
        }
        pendingAudio = audio;
        long measured = files.durationMs(audio);
        showSaveEvent(audio, "recording", measured > 0 ? measured : duration, pendingRecordingPurpose);
    }

    private void cancelRecording() {
        uiHandler.removeCallbacks(recordingTimer);
        recordingTimerText = null;
        if (recorder.isRecording()) {
            recorder.cancel();
        }
        files.deleteQuietly(pendingAudio);
        pendingAudio = null;
        toast("已取消录音");
        showHome();
    }

    private void discardSaveDraft() {
        player.stop();
        if (pendingAudio != null) {
            files.deleteQuietly(pendingAudio);
            pendingAudio = null;
        }
    }

    private void pickAudio() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("audio/*");
        startActivityForResult(intent, IMPORT_AUDIO_REQUEST);
    }

    private void pickBackup() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/zip");
        startActivityForResult(intent, IMPORT_BACKUP_REQUEST);
    }

    private void showSaveEvent(File audio, String source, long durationMs, String defaultPurpose) {
        player.stop();
        currentScreen = Screen.SAVE_EVENT;
        LinearLayout root = base(audio == null ? "保存无音频备注" : "保存录音");
        Spinner parrot = spinner(parrotChoices(false), currentParrotId());
        Spinner purpose = spinner(PURPOSES, defaultPurpose);
        String defaultCategory = defaultCategoryForPurpose(defaultPurpose, source);
        Spinner category = spinner(CATEGORIES, defaultCategory);
        Spinner status = spinner(STATUSES, "pending");
        EditText note = input("备注，可选", "");
        TextView categoryHelp = note("");

        root.addView(label("鹦鹉"));
        root.addView(parrot);
        root.addView(label("用途"));
        root.addView(purpose);
        root.addView(label("类别"));
        root.addView(category);
        root.addView(categoryHelp);
        root.addView(label("状态"));
        root.addView(status);
        root.addView(note);
        bindPurposeCategoryRules(purpose, category, categoryHelp, true);

        if (audio != null) {
            root.addView(note("音频时长：" + formatDuration(durationMs)));
            root.addView(secondaryButton("试听 / 暂停", v -> play(audio)));
            root.addView(secondaryButton(source.equals("recording") ? "重新录制" : "重新导入", v -> {
                files.deleteQuietly(audio);
                pendingAudio = null;
                if (source.equals("recording")) requestRecording(defaultPurpose); else pickAudio();
            }));
        }
        root.addView(primaryButton("保存", v -> {
            Choice parrotChoice = selected(parrot);
            Choice purposeChoice = selected(purpose);
            Choice categoryChoice = selected(category);
            Choice statusChoice = selected(status);
            if ("baseline".equals(purposeChoice.id)) {
                categoryChoice = choiceById(CATEGORIES, "normal_chirp");
            }
            String audioPath = audio == null ? "" : files.relativePath(audio);
            String id = store.saveEvent(
                parrotChoice.id,
                categoryChoice.id,
                statusChoice.id,
                purposeChoice.id,
                audioPath,
                source,
                durationMs,
                note.getText().toString()
            );
            pendingAudio = null;
            ParrotEvent saved = store.getEvent(id);
            toast("已保存");
            showPostSave(saved, purposeChoice.id);
        }));
        root.addView(secondaryButton("取消", v -> navigateBack()));
        setRoot(root, 0);
    }

    private void applyPurposeCategoryRules(Spinner purpose, Spinner category, TextView categoryHelp, boolean resetDefaults) {
        Choice purposeChoice = selected(purpose);
        if ("baseline".equals(purposeChoice.id)) {
            selectSpinner(category, "normal_chirp");
            category.setEnabled(false);
            categoryHelp.setText("日常基线默认保存为「正常鸣叫」，避免误改成异常类别。");
            return;
        }
        category.setEnabled(true);
        if (resetDefaults) {
            selectSpinner(category, "unclassified");
        }
        if ("abnormal".equals(purposeChoice.id)) {
            categoryHelp.setText("异常声音可先选「待确认录音」，听完后再改成更具体的类别。");
        } else {
            categoryHelp.setText("无音频备注用于记录食欲、精神、羽毛等肉眼观察，不一定有声音。");
        }
    }

    private void bindPurposeCategoryRules(Spinner purpose, Spinner category, TextView categoryHelp, boolean resetOnFirstBind) {
        applyPurposeCategoryRules(purpose, category, categoryHelp, resetOnFirstBind);
        purpose.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            private boolean skip = true;

            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                if (skip) {
                    skip = false;
                    return;
                }
                applyPurposeCategoryRules(purpose, category, categoryHelp, true);
            }

            @Override
            public void onNothingSelected(AdapterView<?> parent) {
            }
        });
    }

    private String defaultCategoryForPurpose(String purpose, String source) {
        if ("baseline".equals(purpose)) {
            return "normal_chirp";
        }
        return "unclassified";
    }

    private void showPostSave(ParrotEvent saved, String purpose) {
        currentScreen = Screen.POST_SAVE;
        postSaveEventId = saved == null ? null : saved.id;
        postSavePurpose = purpose == null ? "abnormal" : purpose;
        LinearLayout root = base("已保存");
        LinearLayout panel = panel();
        panel.addView(section("下一步"));
        if (saved != null) {
            panel.addView(body(
                categoryLabel(saved.categoryId) + " · " + purposeLabel(saved.purpose) + "\n" +
                formatTime(saved.createdAt)
            ));
        }
        panel.addView(primaryButton("完成，返回首页", v -> showHome()));
        panel.addView(secondaryButton("查看详情", v -> {
            if (postSaveEventId == null) {
                showHome();
                return;
            }
            showDetail(store.getEvent(postSaveEventId), 0, ORIGIN_HOME);
        }));
        if ("manual".equals(postSavePurpose)) {
            panel.addView(secondaryButton("再写一条备注", v -> showSaveEvent(null, "manual", 0L, "manual")));
        } else if ("baseline".equals(postSavePurpose)) {
            panel.addView(secondaryButton("再录一条基线", v -> requestRecording("baseline")));
        } else {
            panel.addView(secondaryButton("再录一条", v -> requestRecording("abnormal")));
        }
        root.addView(panel);
        setRoot(root, 0);
    }

    private void showLibrary(int scrollY) {
        player.stop();
        currentScreen = Screen.LIBRARY;
        LinearLayout root = base("记录库");
        root.addView(secondaryButton("返回首页", v -> showHome()));

        LinearLayout filterPanel = panel();
        filterPanel.addView(section("筛选"));
        filterPanel.addView(secondaryButton(
            libraryFiltersVisible ? "收起筛选" : "显示筛选",
            v -> {
                libraryFiltersVisible = !libraryFiltersVisible;
                showLibrary(0);
            }
        ));
        if (libraryFiltersVisible) {
            Spinner parrotFilter = spinner(parrotChoices(true), filterParrot);
            Spinner categoryFilter = spinner(withAll(CATEGORIES, "全部类别"), filterCategory);
            Spinner purposeFilter = spinner(withAll(PURPOSES, "全部用途"), filterPurpose);
            Spinner statusFilter = spinner(withAll(STATUSES, "全部状态"), filterStatus);
            filterPanel.addView(label("鹦鹉"));
            filterPanel.addView(parrotFilter);
            filterPanel.addView(label("类别"));
            filterPanel.addView(categoryFilter);
            filterPanel.addView(label("用途"));
            filterPanel.addView(purposeFilter);
            filterPanel.addView(label("状态"));
            filterPanel.addView(statusFilter);
            filterPanel.addView(primaryButton("应用筛选", v -> {
                filterParrot = selected(parrotFilter).id;
                filterCategory = selected(categoryFilter).id;
                filterPurpose = selected(purposeFilter).id;
                filterStatus = selected(statusFilter).id;
                showLibrary(0);
            }));
            filterPanel.addView(secondaryButton("清空筛选", v -> {
                filterParrot = "all";
                filterCategory = "all";
                filterPurpose = "all";
                filterStatus = "all";
                showLibrary(0);
            }));
        } else if (hasActiveFilters()) {
            filterPanel.addView(note("已启用筛选。点「显示筛选」可调整。"));
        }
        root.addView(filterPanel);

        List<ParrotEvent> events = store.listEvents(filterParrot, filterCategory, filterPurpose, filterStatus);
        if (events.isEmpty()) {
            LinearLayout empty = panel();
            if (hasActiveFilters()) {
                empty.addView(note("暂无匹配条目。"));
                empty.addView(secondaryButton("清空筛选", v -> {
                    filterParrot = "all";
                    filterCategory = "all";
                    filterPurpose = "all";
                    filterStatus = "all";
                    showLibrary(0);
                }));
            } else {
                empty.addView(note("记录库还是空的。先录一条日常基线，或录制一段异常声音。"));
                empty.addView(primaryButton("录制日常基线", v -> requestRecording("baseline")));
                empty.addView(secondaryButton("录制异常声音", v -> requestRecording("abnormal")));
            }
            root.addView(empty);
        } else {
            for (ParrotEvent event : events) {
                root.addView(eventRow(event, ORIGIN_LIBRARY));
            }
        }
        setRoot(root, scrollY);
    }

    private boolean hasActiveFilters() {
        return !"all".equals(filterParrot)
            || !"all".equals(filterCategory)
            || !"all".equals(filterPurpose)
            || !"all".equals(filterStatus);
    }

    private void showDetail(ParrotEvent event, int scrollY, String origin) {
        if (event == null) {
            if (ORIGIN_LIBRARY.equals(detailOrigin)) {
                showLibrary(0);
            } else {
                showHome();
            }
            return;
        }
        player.stop();
        currentScreen = Screen.DETAIL;
        detailOrigin = origin == null ? ORIGIN_HOME : origin;
        LinearLayout root = base("条目详情");
        Spinner parrot = spinner(parrotChoices(false), event.parrotId);
        Spinner purpose = spinner(PURPOSES, event.purpose);
        Spinner category = spinner(CATEGORIES, event.categoryId);
        Spinner status = spinner(STATUSES, event.status);
        EditText note = input("备注", event.note);
        root.addView(body("创建时间：" + formatTime(event.createdAt) + "\n来源：" + sourceLabel(event.source) + "\n音频：" + (event.audioPath == null || event.audioPath.length() == 0 ? "无音频" : formatDuration(event.durationMs))));
        if (event.audioPath != null && event.audioPath.length() > 0) {
            File audio = files.resolve(event.audioPath);
            if (audio != null && audio.exists()) {
                root.addView(secondaryButton("播放 / 暂停", v -> play(audio)));
                if ("baseline".equals(event.purpose)) {
                    root.addView(note("这条作为日常基线，可供后续异常声音对比。"));
                } else {
                    root.addView(primaryButton("与日常基线对比", v -> compareWithBaseline(event)));
                }
            } else {
                root.addView(note("音频文件缺失，仍可编辑或删除。"));
            }
        }
        TextView categoryHelp = note("");
        root.addView(label("鹦鹉"));
        root.addView(parrot);
        root.addView(label("用途"));
        root.addView(purpose);
        root.addView(label("类别"));
        root.addView(category);
        root.addView(categoryHelp);
        root.addView(label("状态"));
        root.addView(status);
        root.addView(note);
        bindPurposeCategoryRules(purpose, category, categoryHelp, false);
        root.addView(primaryButton("保存修改", v -> {
            event.parrotId = selected(parrot).id;
            event.purpose = selected(purpose).id;
            event.categoryId = selected(category).id;
            event.status = selected(status).id;
            event.note = note.getText().toString();
            if ("baseline".equals(event.purpose)) {
                event.categoryId = "normal_chirp";
            }
            store.updateEvent(event);
            toast("已保存修改");
            showDetail(store.getEvent(event.id), currentScrollY(), detailOrigin);
        }));
        String backLabel = ORIGIN_LIBRARY.equals(detailOrigin) ? "返回记录库" : "返回首页";
        root.addView(secondaryButton(backLabel, v -> navigateBack()));
        root.addView(dangerButton("删除", v -> confirmDelete(event)));
        setRoot(root, scrollY);
    }

    private void confirmDelete(ParrotEvent event) {
        new AlertDialog.Builder(this)
            .setTitle("删除条目")
            .setMessage("删除后无法恢复。")
            .setNegativeButton("取消", null)
            .setPositiveButton("删除", (dialog, which) -> {
                File audio = files.resolve(event.audioPath);
                store.deleteEvent(event.id);
                files.deleteQuietly(audio);
                toast("已删除");
                if (ORIGIN_LIBRARY.equals(detailOrigin)) {
                    showLibrary(0);
                } else {
                    showHome();
                }
            })
            .show();
    }

    private void compareWithBaseline(ParrotEvent event) {
        File currentAudio = files.resolve(event.audioPath);
        List<ParrotEvent> baselineEvents = store.baselineAudioEvents(event.parrotId, event.id, 5);
        if (currentAudio == null || !currentAudio.isFile()) {
            toast("当前音频文件不可用");
            return;
        }
        if (baselineEvents.isEmpty()) {
            new AlertDialog.Builder(this)
                .setTitle("还没有日常基线")
                .setMessage("请先为这只鹦鹉录制日常状态下的声音。建议在相似距离和环境下积累至少 3 条。")
                .setNegativeButton("稍后", null)
                .setPositiveButton("去录制", (dialog, which) -> requestRecording("baseline"))
                .show();
            return;
        }

        comparisonEventId = event.id;
        currentScreen = Screen.COMPARISON;
        LinearLayout loading = base("声音变化对比");
        loading.addView(note("正在本机分析当前录音，并与最近的日常基线比较…"));
        loading.addView(secondaryButton("返回详情", v -> navigateBack()));
        setRoot(loading, 0);

        new Thread(() -> {
            try {
                AudioFeatures current = featureExtractor.extract(currentAudio);
                List<AudioFeatures> references = new ArrayList<>();
                for (ParrotEvent baselineEvent : baselineEvents) {
                    File baselineAudio = files.resolve(baselineEvent.audioPath);
                    if (baselineAudio == null || !baselineAudio.isFile()) continue;
                    try {
                        references.add(featureExtractor.extract(baselineAudio));
                    } catch (IOException ignored) {
                        // A damaged reference is skipped; valid baseline recordings still participate.
                    }
                }
                if (references.isEmpty()) throw new IOException("日常基线音频不可用");
                BaselineComparison.Result result = BaselineComparison.compare(current, references);
                runOnUiThread(() -> showComparisonResult(event, result));
            } catch (IOException | RuntimeException error) {
                runOnUiThread(() -> {
                    toast("声音对比失败：" + error.getMessage());
                    showDetail(store.getEvent(event.id), 0, detailOrigin);
                });
            }
        }, "parrot-audio-comparison").start();
    }

    private void showComparisonResult(ParrotEvent event, BaselineComparison.Result result) {
        comparisonEventId = event.id;
        currentScreen = Screen.COMPARISON;
        LinearLayout root = base("声音变化对比");
        LinearLayout summary = panel();
        summary.addView(section(result.level));
        summary.addView(body("参考了同一只鹦鹉最近 " + result.referenceCount + " 条有效日常基线。"));
        if (result.referenceCount < 3) {
            summary.addView(note("当前参考较少，建议积累至少 3 条日常基线后再判断趋势。"));
        }
        root.addView(summary);

        LinearLayout details = panel();
        details.addView(section("变化明细"));
        details.addView(body(
            "整体响度：" + signed(result.loudnessDelta, " dB") + "\n" +
            "声音活跃占比：" + signed(result.activityDelta * 100.0d, " 个百分点") + "\n" +
            "声音峰值：" + signed(result.peakDelta, " dB")
        ));
        details.addView(body("正数表示比日常基线更响或更活跃，负数表示更轻或更安静。"));
        root.addView(details);

        LinearLayout guidance = panel();
        guidance.addView(section("如何使用结果"));
        guidance.addView(body(
            "先确认录音距离、手机位置和环境噪声是否与基线接近。若变化持续出现，再结合食欲、精神、羽毛和排泄情况写无音频备注；必要时咨询专业兽医。"
        ));
        guidance.addView(note("这是本地声音变化提示，不是疾病识别或医疗诊断。"));
        root.addView(guidance);
        root.addView(primaryButton("返回条目详情", v -> navigateBack()));
        setRoot(root, 0);
    }

    private String signed(double value, String unit) {
        return String.format(Locale.CHINA, "%+.1f%s", value, unit);
    }

    private void exportBackup() {
        try {
            File backup = backupStore.exportBackup();
            Uri uri = Uri.parse("content://com.parrotcare.mobile.files/" + files.relativePath(backup));
            Intent share = new Intent(Intent.ACTION_SEND);
            share.setType("application/zip");
            share.putExtra(Intent.EXTRA_STREAM, uri);
            share.putExtra(Intent.EXTRA_TITLE, backup.getName());
            share.setClipData(ClipData.newUri(getContentResolver(), backup.getName(), uri));
            share.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(Intent.createChooser(share, "导出数据备份"));
        } catch (IOException error) {
            toast("导出失败：" + error.getMessage());
        }
    }

    private void confirmImportBackup(Uri uri) {
        new AlertDialog.Builder(this)
            .setTitle("导入数据备份")
            .setMessage("导入会新增档案和记录，不会覆盖或删除现有数据。如果备份与本机内容相近，可能出现重复条目。确定继续？")
            .setNegativeButton("取消", null)
            .setPositiveButton("导入", (dialog, which) -> importBackup(uri))
            .show();
    }

    private void importBackup(Uri uri) {
        try {
            BackupStore.ImportResult result = backupStore.importBackup(uri);
            toast("导入完成：档案 " + result.parrots + "，记录 " + result.events + "，跳过 " + result.skipped);
            showHome();
        } catch (IOException error) {
            toast("导入失败：" + error.getMessage());
        }
    }

    private LinearLayout eventRow(ParrotEvent event, String origin) {
        LinearLayout panel = panel();
        panel.setOnClickListener(v -> showDetail(store.getEvent(event.id), 0, origin));
        panel.addView(section(categoryLabel(event.categoryId) + " · " + purposeLabel(event.purpose)));
        panel.addView(body(event.parrotName + " · " + statusLabel(event.status) + " · " + formatTime(event.createdAt) + "\n" + (event.audioPath == null || event.audioPath.length() == 0 ? "无音频" : formatDuration(event.durationMs)) + shortNote(event.note)));
        return panel;
    }

    private void play(File audio) {
        try {
            player.play(audio);
        } catch (IOException | RuntimeException error) {
            toast("音频无法播放");
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == RECORD_AUDIO_REQUEST) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startRecording();
            } else {
                toast("未授予麦克风权限，仍可导入音频或写无音频备注。");
            }
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null || data.getData() == null) {
            return;
        }
        Uri uri = data.getData();
        if (requestCode == IMPORT_AUDIO_REQUEST) {
            try {
                File audio = files.copyFromUri(uri);
                long duration = files.durationMs(audio);
                if (audio.length() < MIN_AUDIO_BYTES || duration < MIN_AUDIO_DURATION_MS) {
                    files.deleteQuietly(audio);
                    toast("导入音频太短或无法识别，未保存");
                    return;
                }
                pendingAudio = audio;
                showSaveEvent(audio, "import", duration, "abnormal");
            } catch (IOException error) {
                toast("导入音频失败：" + error.getMessage());
            }
        } else if (requestCode == IMPORT_BACKUP_REQUEST) {
            confirmImportBackup(uri);
        }
    }

    @Override
    protected void onStop() {
        uiHandler.removeCallbacks(recordingTimer);
        recordingTimerText = null;
        if (recorder.isRecording()) {
            recorder.cancel();
            files.deleteQuietly(pendingAudio);
            pendingAudio = null;
            recordingInterrupted = true;
        }
        super.onStop();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (recordingInterrupted) {
            recordingInterrupted = false;
            showHome();
            new AlertDialog.Builder(this)
                .setTitle("录音已中断")
                .setMessage("应用进入后台时录音已停止，未保存的内容已丢弃。可重新开始录制。")
                .setPositiveButton("知道了", null)
                .show();
        }
    }

    @Override
    protected void onDestroy() {
        uiHandler.removeCallbacks(recordingTimer);
        player.stop();
        store.close();
        super.onDestroy();
    }

    private void ensureCurrentParrot() {
        String current = preferences.getString(PREF_CURRENT_PARROT, "");
        if (current.length() == 0 || store.getParrot(current) == null) {
            setCurrentParrot(store.ensureDefaultParrot());
        }
    }

    private String currentParrotId() {
        ensureCurrentParrot();
        return preferences.getString(PREF_CURRENT_PARROT, store.ensureDefaultParrot());
    }

    private void setCurrentParrot(String id) {
        preferences.edit().putString(PREF_CURRENT_PARROT, id).apply();
    }

    private Choice[] parrotChoices(boolean includeAll) {
        List<ParrotProfile> parrots = store.listParrots();
        Choice[] choices = new Choice[parrots.size() + (includeAll ? 1 : 0)];
        int offset = 0;
        if (includeAll) {
            choices[0] = new Choice("all", "全部鹦鹉");
            offset = 1;
        }
        for (int index = 0; index < parrots.size(); index++) {
            ParrotProfile parrot = parrots.get(index);
            choices[index + offset] = new Choice(parrot.id, parrot.name);
        }
        return choices;
    }

    private Choice[] withAll(Choice[] source, String label) {
        Choice[] choices = new Choice[source.length + 1];
        choices[0] = new Choice("all", label);
        System.arraycopy(source, 0, choices, 1, source.length);
        return choices;
    }

    private Spinner spinner(Choice[] choices, String selectedId) {
        Spinner spinner = new Spinner(this);
        ArrayAdapter<Choice> adapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, choices);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);
        selectSpinner(spinner, selectedId);
        return spinner;
    }

    private void selectSpinner(Spinner spinner, String selectedId) {
        ArrayAdapter<?> adapter = (ArrayAdapter<?>) spinner.getAdapter();
        if (adapter == null) {
            return;
        }
        for (int index = 0; index < adapter.getCount(); index++) {
            Object item = adapter.getItem(index);
            if (item instanceof Choice && ((Choice) item).id.equals(selectedId)) {
                spinner.setSelection(index);
                return;
            }
        }
    }

    private Choice selected(Spinner spinner) {
        return (Choice) spinner.getSelectedItem();
    }

    private Choice choiceById(Choice[] choices, String id) {
        for (Choice choice : choices) {
            if (choice.id.equals(id)) {
                return choice;
            }
        }
        return choices[0];
    }

    private LinearLayout base(String title) {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(20), dp(18), dp(24));
        root.setBackgroundColor(Color.rgb(242, 245, 242));
        TextView heading = new TextView(this);
        heading.setText(title);
        heading.setTextSize(26);
        heading.setTextColor(Color.rgb(23, 33, 29));
        heading.setGravity(Gravity.START);
        heading.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        root.addView(heading);
        return root;
    }

    private void setRoot(LinearLayout root, int scrollY) {
        ScrollView scroll = new ScrollView(this);
        scroll.addView(root);
        currentScrollView = scroll;
        setContentView(scroll);
        if (scrollY > 0) scroll.post(() -> scroll.scrollTo(0, scrollY));
    }

    private int currentScrollY() {
        return currentScrollView == null ? 0 : currentScrollView.getScrollY();
    }

    private LinearLayout panel() {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(14), dp(12), dp(14), dp(12));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        params.setMargins(0, dp(10), 0, 0);
        panel.setLayoutParams(params);
        panel.setBackgroundColor(Color.WHITE);
        return panel;
    }

    private TextView section(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(17);
        view.setTextColor(Color.rgb(23, 33, 29));
        view.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        view.setPadding(0, dp(8), 0, dp(4));
        return view;
    }

    private TextView label(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextColor(Color.rgb(60, 72, 66));
        view.setTextSize(14);
        view.setPadding(0, dp(10), 0, dp(2));
        return view;
    }

    private TextView body(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(15);
        view.setTextColor(Color.rgb(75, 87, 81));
        view.setPadding(0, dp(6), 0, dp(4));
        return view;
    }

    private TextView note(String text) {
        TextView view = body(text);
        view.setTextColor(Color.rgb(23, 107, 77));
        return view;
    }

    private EditText input(String hint, String value) {
        EditText edit = new EditText(this);
        edit.setHint(hint);
        edit.setText(value);
        edit.setSingleLine(false);
        edit.setMinLines(1);
        edit.setTextSize(15);
        return edit;
    }

    private Button primaryButton(String text, View.OnClickListener listener) {
        Button button = button(text, listener);
        button.setBackgroundColor(Color.rgb(23, 107, 77));
        button.setTextColor(Color.WHITE);
        return button;
    }

    private Button secondaryButton(String text, View.OnClickListener listener) {
        Button button = button(text, listener);
        button.setBackgroundColor(Color.rgb(225, 237, 231));
        button.setTextColor(Color.rgb(23, 107, 77));
        return button;
    }

    private Button dangerButton(String text, View.OnClickListener listener) {
        Button button = button(text, listener);
        button.setBackgroundColor(Color.rgb(180, 58, 58));
        button.setTextColor(Color.WHITE);
        return button;
    }

    private Button button(String text, View.OnClickListener listener) {
        Button button = new Button(this);
        button.setText(text);
        button.setAllCaps(false);
        button.setOnClickListener(listener);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(48));
        params.setMargins(0, dp(10), 0, 0);
        button.setLayoutParams(params);
        return button;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }

    private String categoryLabel(String id) {
        return labelFor(CATEGORIES, id);
    }

    private String statusLabel(String id) {
        return labelFor(STATUSES, id);
    }

    private String purposeLabel(String id) {
        return labelFor(PURPOSES, id);
    }

    private String labelFor(Choice[] choices, String id) {
        for (Choice choice : choices) {
            if (choice.id.equals(id)) return choice.label;
        }
        return id == null ? "" : id;
    }

    private String sourceLabel(String source) {
        if ("recording".equals(source)) return "录音";
        if ("import".equals(source)) return "导入";
        return "无音频备注";
    }

    private String formatTime(long millis) {
        return new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.CHINA).format(new Date(millis));
    }

    private String formatDuration(long millis) {
        long seconds = Math.max(0L, millis / 1000L);
        return seconds / 60 + "分" + seconds % 60 + "秒";
    }

    private String shortNote(String note) {
        if (note == null || note.trim().length() == 0) return "";
        String clean = note.trim().replace('\n', ' ');
        if (clean.length() > 28) clean = clean.substring(0, 28) + "…";
        return "\n备注：" + clean;
    }

    private String emptyLabel(String value) {
        return value == null || value.trim().length() == 0 ? "未填写" : value.trim();
    }

    private static final class Choice {
        final String id;
        final String label;

        Choice(String id, String label) {
            this.id = id;
            this.label = label;
        }

        @Override
        public String toString() {
            return label;
        }
    }
}
