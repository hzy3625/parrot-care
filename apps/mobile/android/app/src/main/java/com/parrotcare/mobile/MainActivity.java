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
import android.view.Gravity;
import android.view.View;
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
import com.parrotcare.mobile.data.AudioFileStore;
import com.parrotcare.mobile.data.BackupStore;
import com.parrotcare.mobile.data.LocalStore;
import com.parrotcare.mobile.data.LocalStore.ParrotEvent;
import com.parrotcare.mobile.data.LocalStore.ParrotProfile;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final int RECORD_AUDIO_REQUEST = 100;
    private static final int IMPORT_AUDIO_REQUEST = 101;
    private static final int IMPORT_BACKUP_REQUEST = 102;
    private static final String PREFS = "parrotcare";
    private static final String PREF_CURRENT_PARROT = "current_parrot_id";

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
        new Choice("abnormal", "异常观察"),
        new Choice("manual", "无音频观察")
    };

    private final AudioRecorder recorder = new AudioRecorder();
    private final AudioPlayer player = new AudioPlayer();
    private LocalStore store;
    private AudioFileStore files;
    private BackupStore backupStore;
    private SharedPreferences preferences;
    private ScrollView currentScrollView;
    private File pendingAudio;
    private long recordingStartedAt;
    private String filterParrot = "all";
    private String filterCategory = "all";
    private String filterPurpose = "all";
    private String filterStatus = "all";

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

    private void showHome() {
        player.stop();
        LinearLayout root = base("ParrotCare");
        root.addView(note("本地优先的鹦鹉声音与健康观察记录。核心功能离线可用。"));

        root.addView(card("记录", "高频操作：录制声音、导入音频或记录无音频观察。"));
        root.addView(primaryButton("录制声音", v -> requestRecording()));
        root.addView(secondaryButton("导入音频", v -> pickAudio()));
        root.addView(secondaryButton("新建观察", v -> showSaveEvent(null, "manual", 0L, "manual")));

        root.addView(card("记录库", "查看最近记录或进入全部记录。"));
        List<ParrotEvent> recent = store.recentEvents(5);
        if (recent.isEmpty()) {
            root.addView(note("暂无记录。"));
        } else {
            for (ParrotEvent event : recent) {
                root.addView(eventRow(event, store.recentEvents(5)));
            }
        }
        root.addView(primaryButton("查看全部记录", v -> showLibrary(0)));

        root.addView(card("数据和设置", "低频操作：管理鹦鹉档案、导出和导入备份。"));
        root.addView(secondaryButton("鹦鹉档案", v -> showParrots()));
        root.addView(secondaryButton("导出数据备份", v -> exportBackup()));
        root.addView(secondaryButton("导入数据备份", v -> pickBackup()));

        setRoot(root, 0);
    }

    private void showParrots() {
        LinearLayout root = base("鹦鹉档案");
        List<ParrotProfile> parrots = store.listParrots();
        String currentId = currentParrotId();
        root.addView(note("当前鹦鹉会作为新记录的默认归属。"));
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
        root.addView(secondaryButton("返回档案", v -> showParrots()));
        setRoot(root, 0);
    }

    private void requestRecording() {
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
            showRecording();
        } catch (IOException | RuntimeException error) {
            files.deleteQuietly(pendingAudio);
            pendingAudio = null;
            toast("录音启动失败");
        }
    }

    private void showRecording() {
        LinearLayout root = base("正在录音");
        root.addView(note("录音中。停止后可试听，再决定是否保存。"));
        root.addView(primaryButton("停止录音", v -> stopRecording()));
        root.addView(secondaryButton("取消录音", v -> cancelRecording()));
        setRoot(root, 0);
    }

    private void stopRecording() {
        File audio = recorder.stop();
        long duration = System.currentTimeMillis() - recordingStartedAt;
        if (audio == null || !audio.exists() || audio.length() <= 0 || duration < 800L) {
            files.deleteQuietly(audio);
            pendingAudio = null;
            toast("录音太短或无效，未保存");
            showHome();
            return;
        }
        pendingAudio = audio;
        long measured = files.durationMs(audio);
        showSaveEvent(audio, "recording", measured > 0 ? measured : duration, "abnormal");
    }

    private void cancelRecording() {
        if (recorder.isRecording()) {
            recorder.cancel();
        }
        files.deleteQuietly(pendingAudio);
        pendingAudio = null;
        toast("已取消录音");
        showHome();
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
        LinearLayout root = base(audio == null ? "保存观察" : "保存声音记录");
        Spinner parrot = spinner(parrotChoices(false), currentParrotId());
        Spinner purpose = spinner(PURPOSES, defaultPurpose);
        Spinner category = spinner(CATEGORIES, source.equals("manual") ? "unclassified" : "unclassified");
        Spinner status = spinner(STATUSES, "pending");
        EditText note = input("备注，可选", "");
        root.addView(label("鹦鹉"));
        root.addView(parrot);
        root.addView(label("记录用途"));
        root.addView(purpose);
        root.addView(label("类别"));
        root.addView(category);
        root.addView(label("状态"));
        root.addView(status);
        root.addView(note);
        if (audio != null) {
            root.addView(note("音频时长：" + formatDuration(durationMs)));
            root.addView(secondaryButton("试听 / 暂停", v -> play(audio)));
            root.addView(secondaryButton(source.equals("recording") ? "重新录制" : "重新导入", v -> {
                files.deleteQuietly(audio);
                pendingAudio = null;
                if (source.equals("recording")) requestRecording(); else pickAudio();
            }));
        }
        root.addView(primaryButton("保存记录", v -> {
            Choice parrotChoice = selected(parrot);
            Choice purposeChoice = selected(purpose);
            Choice categoryChoice = selected(category);
            Choice statusChoice = selected(status);
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
            showDetail(saved, 0);
        }));
        root.addView(secondaryButton("取消", v -> {
            if (audio != null) files.deleteQuietly(audio);
            pendingAudio = null;
            showHome();
        }));
        setRoot(root, 0);
    }

    private void showLibrary(int scrollY) {
        player.stop();
        LinearLayout root = base("记录库");
        root.addView(secondaryButton("返回首页", v -> showHome()));
        Spinner parrotFilter = spinner(parrotChoices(true), filterParrot);
        Spinner categoryFilter = spinner(withAll(CATEGORIES, "全部类别"), filterCategory);
        Spinner purposeFilter = spinner(withAll(PURPOSES, "全部用途"), filterPurpose);
        Spinner statusFilter = spinner(withAll(STATUSES, "全部状态"), filterStatus);
        root.addView(label("鹦鹉"));
        root.addView(parrotFilter);
        root.addView(label("类别"));
        root.addView(categoryFilter);
        root.addView(label("用途"));
        root.addView(purposeFilter);
        root.addView(label("状态"));
        root.addView(statusFilter);
        root.addView(primaryButton("应用筛选", v -> {
            filterParrot = selected(parrotFilter).id;
            filterCategory = selected(categoryFilter).id;
            filterPurpose = selected(purposeFilter).id;
            filterStatus = selected(statusFilter).id;
            showLibrary(0);
        }));
        root.addView(secondaryButton("清空筛选", v -> {
            filterParrot = "all";
            filterCategory = "all";
            filterPurpose = "all";
            filterStatus = "all";
            showLibrary(0);
        }));

        List<ParrotEvent> events = store.listEvents(filterParrot, filterCategory, filterPurpose, filterStatus);
        if (events.isEmpty()) {
            root.addView(note("暂无匹配记录。"));
        } else {
            for (ParrotEvent event : events) {
                root.addView(eventRow(event, events));
            }
        }
        setRoot(root, scrollY);
    }

    private void showDetail(ParrotEvent event, int scrollY) {
        if (event == null) {
            showLibrary(0);
            return;
        }
        player.stop();
        LinearLayout root = base("记录详情");
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
            } else {
                root.addView(note("音频文件缺失，仍可编辑或删除记录。"));
            }
        }
        root.addView(label("鹦鹉"));
        root.addView(parrot);
        root.addView(label("记录用途"));
        root.addView(purpose);
        root.addView(label("类别"));
        root.addView(category);
        root.addView(label("状态"));
        root.addView(status);
        root.addView(note);
        root.addView(primaryButton("保存修改", v -> {
            event.parrotId = selected(parrot).id;
            event.purpose = selected(purpose).id;
            event.categoryId = selected(category).id;
            event.status = selected(status).id;
            event.note = note.getText().toString();
            store.updateEvent(event);
            toast("已保存修改");
            showDetail(store.getEvent(event.id), currentScrollY());
        }));
        root.addView(secondaryButton("返回记录库", v -> showLibrary(0)));
        root.addView(dangerButton("删除记录", v -> confirmDelete(event)));
        setRoot(root, scrollY);
    }

    private void confirmDelete(ParrotEvent event) {
        new AlertDialog.Builder(this)
            .setTitle("删除记录")
            .setMessage("删除后无法恢复。")
            .setNegativeButton("取消", null)
            .setPositiveButton("删除", (dialog, which) -> {
                File audio = files.resolve(event.audioPath);
                store.deleteEvent(event.id);
                files.deleteQuietly(audio);
                toast("已删除");
                showLibrary(0);
            })
            .show();
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

    private void importBackup(Uri uri) {
        try {
            BackupStore.ImportResult result = backupStore.importBackup(uri);
            toast("导入完成：档案 " + result.parrots + "，记录 " + result.events + "，跳过 " + result.skipped);
            showHome();
        } catch (IOException error) {
            toast("导入失败：" + error.getMessage());
        }
    }

    private LinearLayout eventRow(ParrotEvent event, List<ParrotEvent> sourceList) {
        LinearLayout panel = panel();
        panel.setOnClickListener(v -> showDetail(store.getEvent(event.id), 0));
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
                toast("未授予麦克风权限，仍可导入音频或新建观察。");
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
                showSaveEvent(audio, "import", duration, "abnormal");
            } catch (IOException error) {
                toast("导入音频失败：" + error.getMessage());
            }
        } else if (requestCode == IMPORT_BACKUP_REQUEST) {
            importBackup(uri);
        }
    }

    @Override
    protected void onStop() {
        if (recorder.isRecording()) {
            recorder.cancel();
            files.deleteQuietly(pendingAudio);
            pendingAudio = null;
        }
        super.onStop();
    }

    @Override
    protected void onDestroy() {
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
        for (int index = 0; index < choices.length; index++) {
            if (choices[index].id.equals(selectedId)) {
                spinner.setSelection(index);
                break;
            }
        }
        return spinner;
    }

    private Choice selected(Spinner spinner) {
        return (Choice) spinner.getSelectedItem();
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

    private TextView card(String title, String description) {
        TextView view = body(title + "\n" + description);
        view.setTextColor(Color.rgb(23, 33, 29));
        view.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        return view;
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
        return "手动观察";
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
