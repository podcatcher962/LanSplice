package com.lanlan.lansplice;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.ContentResolver;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import android.text.InputFilter;
import android.text.InputType;
import android.text.TextUtils;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.DownloadListener;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.URL;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map;


/**
 * LanSplice 安卓客户端。
 *
 * 只做三件事：
 *   1. 找到局域网里的电脑（UDP 广播，和桌面端同一个 DISCOVERY_PORT）；
 *   2. 用配对码算出网页令牌，把电脑端那个手机页面装进 WebView；
 *   3. 接住系统分享菜单送来的文件，直接 POST 到电脑的 /up 接口。
 *
 * 为什么第 3 条要原生做：安卓分享菜单给出的是 content:// URI，
 * WebView 里的网页拿不到它；而且分享场景下用户不希望再点开网页选一次文件。
 *
 * 为什么要自己算令牌：网页令牌由配对码派生（HMAC-SHA256），
 * 所以只要用户抄一次配对码，之后任何时候都能连，不必再扫码。
 * 令牌不参与 47820 那条加密通道的握手，泄漏也打不开文件传输。
 */
public class MainActivity extends Activity {

    // ---------------------------------------------------------------- 常量

    static final int DISCOVERY_PORT = 47821;
    static final int DEFAULT_WEB_PORT = 47822;   // 与 link2pc_web.WEB_PORT 一致
    static final String PROBE = "L2P-DISCOVER1";
    static final String OFFER = "L2P-OFFER";

    // 颜色不是常量了：跟随浅色/深色两套，在建界面之前由 loadPalette() 定下来
    int C_BG, C_CARD, C_TEXT, C_SUB, C_LINE, C_PURPLE, C_GRAY, C_GREEN, C_RED;
    int C_FIELD, C_DIV;

    static final String[] THEMES = {"auto", "light", "dark"};

    private boolean isDark() {
        String t = sp.getString("theme", "auto");
        if ("dark".equals(t)) {
            return true;
        }
        if ("light".equals(t)) {
            return false;
        }
        int mode = getResources().getConfiguration().uiMode
                & Configuration.UI_MODE_NIGHT_MASK;
        return mode == Configuration.UI_MODE_NIGHT_YES;
    }

    private void loadPalette() {
        if (isDark()) {
            C_BG = 0xFF14191C;
            C_CARD = 0xFF1D2529;
            C_TEXT = 0xFFE6ECEF;
            C_SUB = 0xFF9FB0B8;
            C_LINE = 0xFF33403E;
            C_FIELD = 0xFF243038;
            C_DIV = 0xFF2A343A;
            C_PURPLE = 0xFF8E5CD0;
            C_GRAY = 0xFF4E5F6B;
            C_GREEN = 0xFF4C9E51;
            C_RED = 0xFFB85454;
        } else {
            C_BG = 0xFFECEFF1;
            C_CARD = 0xFFFFFFFF;
            C_TEXT = 0xFF1F2A30;
            C_SUB = 0xFF5F7079;
            C_LINE = 0xFFD5DDE2;
            C_FIELD = 0xFFFFFFFF;
            C_DIV = 0xFFEEF2F4;
            C_PURPLE = 0xFF6A1B9A;
            C_GRAY = 0xFF607D8B;
            C_GREEN = 0xFF2E7D32;
            C_RED = 0xFFC62828;
        }
    }

    private String themeLabel() {
        String t = sp.getString("theme", "auto");
        if ("dark".equals(t)) {
            return "深色";
        }
        if ("light".equals(t)) {
            return "浅色";
        }
        return "跟随系统";
    }

    // ---------------------------------------------------------------- 状态

    WebView web;
    ScrollView pageSetup;
    FrameLayout pageWeb;
    LinearLayout devList;
    View setupInner;
    EditText edCode;
    EditText edHost;
    TextView tvMsg;
    TextView tvTip;
    TextView tvDir;
    TextView tvTheme;
    TextView tvOverlay;
    TextView errView;

    /** 已连上的电脑。token 只在点「连接」时算一次。 */
    volatile String token = "";
    volatile String host = "";
    volatile int webPort = DEFAULT_WEB_PORT;
    volatile String pcName = "";

    /** 分享菜单送进来、还没送出去的文件。 */
    final ArrayList<Uri> pending = new ArrayList<Uri>();

    final Handler ui = new Handler(Looper.getMainLooper());
    SharedPreferences sp;

    /** 上次界面用的是不是深色。系统主题一变就靠它判断要不要重建。 */
    boolean wasDark;

    ValueCallback<Uri[]> filePathCallback;
    static final int REQ_FILE = 0x51;
    static final int REQ_DIR = 0x52;

    // ---------------------------------------------------------------- 生命周期

    @Override
    protected void onCreate(Bundle b) {
        // 整个启动都包在 try 里：闪退时用户至少能看到原因，而不是白屏一下没了
        try {
            super.onCreate(b);
            Thread.setDefaultUncaughtExceptionHandler(new Thread.UncaughtExceptionHandler() {
                public void uncaughtException(Thread t, Throwable e) {
                    try {
                        saveCrash(e);
                    } catch (Throwable ignored) {
                    }
                    android.os.Process.killProcess(android.os.Process.myPid());
                }
            });
            sp = getSharedPreferences("lansplice", MODE_PRIVATE);
            loadPalette();
            wasDark = isDark();
            buildUi();
            String crash = readLastCrash();
            if (crash != null) {
                showText("上次启动出错了：\n\n" + crash, true);
            }
            // 换配色会重建界面，正在看文件页的人不该被丢回配对页
            if (sp.getBoolean("resume_web", false)) {
                sp.edit().putBoolean("resume_web", false).apply();
                String h = sp.getString("host", "");
                if (h.length() > 0 && edCode.getText().toString().trim().length() >= 16) {
                    connectTo(h, DEFAULT_WEB_PORT, "");
                }
            }
            handleIntent(getIntent());
        } catch (Throwable e) {
            showCrashNow(e);
        }
    }

    @Override
    protected void onNewIntent(Intent it) {
        super.onNewIntent(it);
        setIntent(it);
        handleIntent(it);
    }

    /**
     * 系统主题在 App 运行中被切换。
     *
     * 选了「跟随系统」的人，默认期望 App 跟着变；选了浅色/深色的人不该被搅。
     * 这里只比一次「深色与否」，变了才 recreate —— 否则每次细微的配置变化
     * （比如插拔耳机改的 uiMode 位）都会重建界面，正在传的文件会断。
     */
    @Override
    public void onConfigurationChanged(Configuration cfg) {
        super.onConfigurationChanged(cfg);
        if (!"auto".equals(sp.getString("theme", "auto"))) {
            return;
        }
        if (isDark() != wasDark) {
            recreateKeepingPage();
        }
    }

    /**
     * 状态栏 / 导航栏配色。
     *
     * 只改窗口背景不够：状态栏默认是系统给的黑底白字，深色主题下会跟
     * 页面之间出现一道明显的分界线。这里底部、顶部一起刷成界面底色，
     * 再按深浅切换图标黑/白（API 23 起才有 LIGHT_STATUS_BAR）。
     */
    private void paintSystemBars() {
        try {
            getWindow().setStatusBarColor(C_BG);
        } catch (Throwable ignored) {
        }
        try {
            getWindow().setNavigationBarColor(C_BG);
        } catch (Throwable ignored) {
        }
        try {
            if (Build.VERSION.SDK_INT >= 23) {
                View v = getWindow().getDecorView();
                int f = v.getSystemUiVisibility();
                if (isDark()) {
                    f = f & ~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
                } else {
                    f = f | View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
                }
                // API 26 起导航栏也能用深色图标
                if (Build.VERSION.SDK_INT >= 26) {
                    if (isDark()) {
                        f = f & ~View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
                    } else {
                        f = f | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
                    }
                }
                v.setSystemUiVisibility(f);
            }
        } catch (Throwable ignored) {
        }
    }

    @Override
    protected void onDestroy() {
        try {
            if (web != null) {
                web.destroy();
            }
        } catch (Throwable ignored) {
        }
        super.onDestroy();
    }

    // ---------------------------------------------------------------- 界面

    private int dp(float v) {
        return (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v,
                getResources().getDisplayMetrics());
    }

    private void buildUi() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(C_BG);

        // ---- 连接页
        pageSetup = new ScrollView(this);
        pageSetup.setBackgroundColor(C_BG);
        pageSetup.setFillViewport(true);

        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setPadding(dp(20), dp(28), dp(20), dp(28));
        pageSetup.addView(col, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        setupInner = col;

        TextView h1 = new TextView(this);
        h1.setText("LanSplice");
        h1.setTextColor(C_TEXT);
        h1.setTextSize(28);
        h1.setTypeface(h1.getTypeface(), android.graphics.Typeface.BOLD);
        col.addView(h1);

        TextView sub = new TextView(this);
        sub.setText("手机 ↔ 电脑 · 同一个路由器 · 不经过任何服务器");
        sub.setTextColor(C_SUB);
        sub.setTextSize(13);
        sub.setPadding(0, dp(4), 0, dp(20));
        col.addView(sub);

        // 已经配过对的人，最常做的是「看电脑发来的文件」。
        // 每次都让他从设备列表里再点一次，纯属浪费；这里给个直达按钮。
        final String lastHost = sp.getString("host", "");
        final String lastCode = sp.getString("code", "");
        if (lastHost.length() > 0 && lastCode.trim().length() >= 16) {
            Button open = bigButton("打开电脑上的文件（" + lastHost + "）", C_GREEN);
            open.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    connectTo(lastHost, DEFAULT_WEB_PORT, "");
                }
            });
            col.addView(open);
            TextView hint = new TextView(this);
            hint.setText("电脑上点了「发到手机」的文件，都在这一页。");
            hint.setTextColor(C_SUB);
            hint.setTextSize(12);
            hint.setPadding(0, dp(6), 0, dp(4));
            col.addView(hint);
        }

        col.addView(label("配对码"));
        edCode = mkInput("ABCD-EFGH-JKLM-NPQR", sp.getString("code", ""), true);
        col.addView(edCode);

        TextView codeTip = new TextView(this);
        codeTip.setText("在电脑软件主界面点「本机配对码」抄过来，只需一次。");
        codeTip.setTextColor(C_SUB);
        codeTip.setTextSize(12);
        codeTip.setPadding(0, dp(6), 0, dp(18));
        col.addView(codeTip);

        Button scan = bigButton("搜索局域网电脑", C_PURPLE);
        scan.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                doDiscover();
            }
        });
        col.addView(scan);

        tvTip = new TextView(this);
        tvTip.setTextColor(C_SUB);
        tvTip.setTextSize(13);
        tvTip.setPadding(0, dp(14), 0, dp(6));
        col.addView(tvTip);

        devList = new LinearLayout(this);
        devList.setOrientation(LinearLayout.VERTICAL);
        col.addView(devList);

        // 手动输入：路由器开了「AP 隔离」时广播收不到，这条是兜底
        col.addView(label("或手动填电脑地址"));
        edHost = mkInput("192.168.0.108", sp.getString("host", ""), false);
        col.addView(edHost);

        Button manual = bigButton("连接这台电脑", C_GRAY);
        manual.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                String h = edHost.getText().toString().trim();
                if (h.length() == 0) {
                    toast("先填电脑地址");
                    return;
                }
                connectTo(h, DEFAULT_WEB_PORT, "");
            }
        });
        col.addView(manual);

        tvMsg = new TextView(this);
        tvMsg.setTextColor(C_SUB);
        tvMsg.setTextSize(13);
        tvMsg.setPadding(0, dp(16), 0, 0);
        col.addView(tvMsg);

        // ---- 设置：接收目录 / 深浅色
        col.addView(label("电脑发来的文件存到哪"));
        tvDir = settingRow("");
        tvDir.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                pickRecvDir();
            }
        });
        col.addView(tvDir);

        col.addView(label("深浅色"));
        tvTheme = settingRow("");
        tvTheme.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                cycleTheme();
            }
        });
        col.addView(tvTheme);

        TextView ver = new TextView(this);
        ver.setText("LanSplice " + versionName() + " · 手机端");
        ver.setTextColor(C_SUB);
        ver.setTextSize(11);
        ver.setPadding(0, dp(28), 0, 0);
        col.addView(ver);

        // ---- 网页页
        pageWeb = new FrameLayout(this);
        pageWeb.setBackgroundColor(C_BG);
        web = new WebView(this);
        web.setBackgroundColor(C_BG);
        WebSettings ws = web.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);      // 网页用 sessionStorage 存令牌
        ws.setAllowFileAccess(false);
        ws.setAllowContentAccess(false);
        ws.setSupportZoom(true);
        ws.setBuiltInZoomControls(true);
        ws.setDisplayZoomControls(false);
        if (Build.VERSION.SDK_INT >= 21) {
            ws.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        }
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, String url) {
                // 只在自己连的那台电脑里导航，外链交给系统浏览器。
                // 否则页面里点到任何 http 链接都会把这个 WebView 带走，
                // 用户就再也回不到文件页了。
                return !sameHost(url);
            }

            @Override
            public void onPageFinished(WebView v, String url) {
                super.onPageFinished(v, url);
                if (pending.size() > 0) {
                    sendPending();
                }
            }

            // 连不上 / 令牌不对时，别把浏览器的「无法访问此网站」直接甩给用户：
            // 那个页面看不出是网段问题还是配对码问题。这里换成自己的说明。
            @Override
            public void onReceivedError(WebView v, WebResourceRequest req,
                                        WebResourceError er) {
                if (req == null || !req.isForMainFrame()) {
                    return;
                }
                String d = (er == null) ? "" : String.valueOf(er.getDescription());
                showWebError("连不上这台电脑",
                        "地址 " + host + ":" + webPort + "\n" + d
                                + "\n\n常见的三个原因：\n"
                                + "· 手机和电脑不在同一个路由器 / 同网段\n"
                                + "· 电脑上的 LanSplice 已经退出\n"
                                + "· 路由器开了「AP 隔离」，设备之间互相看不见");
            }

            @Override
            public void onReceivedHttpError(WebView v, WebResourceRequest req,
                                            WebResourceResponse res) {
                if (req == null || !req.isForMainFrame() || res == null) {
                    return;
                }
                int sc = res.getStatusCode();
                if (sc == 401 || sc == 403) {
                    showWebError("配对码对不上",
                            "电脑拒绝了这次访问（HTTP " + sc + "）。\n\n"
                                    + "电脑上的配对码可能刚被重置过。回到上一页，"
                                    + "点电脑主界面的「本机配对码」重新抄一次。");
                }
            }
        });
        // WebView 自己不处理下载：不接这个回调，页面上的「下载」点了毫无反应。
        web.setDownloadListener(new DownloadListener() {
            public void onDownloadStart(String url, String ua, String cd,
                                        String mime, long len) {
                startDownload(url, mime);
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView v,
                                             ValueCallback<Uri[]> cb,
                                             FileChooserParams params) {
                // WebView 不会自己弹选择器，必须接住；无论成败都要回调一次，
                // 否则网页里那个 <input type=file> 会永久卡住。
                if (filePathCallback != null) {
                    filePathCallback.onReceiveValue(null);
                }
                filePathCallback = cb;
                try {
                    Intent i = new Intent(Intent.ACTION_GET_CONTENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType("*/*");
                    if (params != null && params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE) {
                        i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
                    }
                    startActivityForResult(Intent.createChooser(i, "选择文件"), REQ_FILE);
                } catch (Exception e) {
                    filePathCallback = null;
                    toast("打不开文件选择器：" + e.getMessage());
                    return false;
                }
                return true;
            }
        });
        pageWeb.addView(web, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        // 连不上时的说明页，盖在 WebView 上
        errView = new TextView(this);
        errView.setTextColor(C_TEXT);
        errView.setTextSize(15);
        errView.setBackgroundColor(C_BG);
        errView.setPadding(dp(24), dp(44), dp(24), dp(24));
        errView.setLineSpacing(dp(4), 1.0f);
        errView.setVisibility(View.GONE);
        errView.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                backToSetup();
            }
        });
        pageWeb.addView(errView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        // 发送进度盖在网页上：分享进来的文件是原生上传的，网页自己看不到
        tvOverlay = new TextView(this);
        tvOverlay.setTextColor(Color.WHITE);
        tvOverlay.setTextSize(14);
        tvOverlay.setBackgroundColor(0xDD1F2A30);
        tvOverlay.setPadding(dp(16), dp(10), dp(16), dp(10));
        tvOverlay.setVisibility(View.GONE);
        FrameLayout.LayoutParams olp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        olp.gravity = Gravity.BOTTOM;
        pageWeb.addView(tvOverlay, olp);

        pageWeb.setVisibility(View.GONE);
        root.addView(pageSetup, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        root.addView(pageWeb, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        setContentView(root);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        refreshSettings();
        paintSystemBars();
    }

    /**
     * 设置区的一行：看起来像个输入框，点一下才动作。
     * 不做成 Button，是因为这几行更像「当前值」，不是主操作。
     */
    private TextView settingRow(String text) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextColor(C_TEXT);
        t.setTextSize(15);
        t.setPadding(dp(14), dp(13), dp(14), dp(13));
        t.setBackground(inputBg());
        t.setMinHeight(dp(48));
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        p.topMargin = dp(6);
        t.setLayoutParams(p);
        return t;
    }

    private void refreshSettings() {
        if (tvDir != null) {
            tvDir.setText(recvDirLabel());
        }
        if (tvTheme != null) {
            tvTheme.setText(themeLabel() + "（点这里切换）");
        }
    }

    /** 选接收目录。用 SAF，这样不需要任何存储权限。 */
    private void pickRecvDir() {
        final String cur = sp.getString("recv_tree", "");
        if (cur.length() == 0) {
            openDirPicker();
            return;
        }
        // 已经选过的人，第二个念头往往是「换回默认」——给个能退回去的路，
        // 否则一旦点了目录选择器就再也没法恢复成系统「下载」目录。
        new AlertDialog.Builder(this)
                .setTitle("电脑发来的文件存到哪")
                .setItems(new String[]{"重新选一个目录", "恢复系统「下载」目录"},
                        new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface d, int i) {
                                if (i == 0) {
                                    openDirPicker();
                                } else {
                                    sp.edit().remove("recv_tree").apply();
                                    refreshSettings();
                                    toast("以后存到系统「下载」目录");
                                }
                            }
                        })
                .setNegativeButton("取消", null)
                .show();
    }

    private void openDirPicker() {
        try {
            Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
            // 没这几个 flag 就拿不到持久写权限，App 重启后目录会失效
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                    | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            startActivityForResult(i, REQ_DIR);
        } catch (Exception e) {
            toast("这台手机没有目录选择器");
        }
    }

    private String recvDirLabel() {
        String t = sp.getString("recv_tree", "");
        if (t.length() == 0) {
            return "系统「下载」目录（点这里改）";
        }
        try {
            Uri u = Uri.parse(t);
            Uri doc = DocumentsContract.buildDocumentUriUsingTree(
                    u, DocumentsContract.getTreeDocumentId(u));
            Cursor c = getContentResolver().query(doc,
                    new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null);
            if (c != null) {
                try {
                    if (c.moveToFirst()) {
                        String n = c.getString(0);
                        if (n != null && n.length() > 0) {
                            return n + "（点这里改）";
                        }
                    }
                } finally {
                    c.close();
                }
            }
        } catch (Exception ignored) {
        }
        return "已选目录（点这里改）";
    }

    /** 跟随系统 -> 浅色 -> 深色 -> 跟随系统。改完重建界面最省事，配色处处生效。 */
    private void cycleTheme() {
        String t = sp.getString("theme", "auto");
        String next = "auto".equals(t) ? "light" : ("light".equals(t) ? "dark" : "auto");
        sp.edit().putString("theme", next).apply();
        recreateKeepingPage();
    }

    /**
     * 重建界面（换配色用）。
     *
     * 重建后 WebView 连同页面一起没了，所以先记一笔「刚才在看文件页」，
     * onCreate 里再自动接回去 —— 否则用户切一下深色，就得重新走一遍连接，
     * 体验上像是被踢出来了。
     */
    private void recreateKeepingPage() {
        boolean onWeb = pageWeb != null && pageWeb.getVisibility() == View.VISIBLE
                && (errView == null || errView.getVisibility() != View.VISIBLE);
        sp.edit().putBoolean("resume_web", onWeb).apply();
        recreate();
    }

    private TextView label(String s) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextColor(C_SUB);
        t.setTextSize(12);
        t.setTypeface(t.getTypeface(), android.graphics.Typeface.BOLD);
        t.setPadding(0, dp(14), 0, dp(2));
        return t;
    }

    /**
     * 输入框。
     *
     * 之前这里踩过一个坑：调用方写 addView(ed, lp(0, dp(6)))，把「上边距」
     * 当成了第二个参数，实际那是**高度**，于是输入框只剩 6dp —— 屏幕上
     * 就是一条白线，用户根本看不出那是个能点的地方，自然也配不上对。
     * 现在统一由本方法给参数，高度 WRAP_CONTENT + 最小 48dp。
     */
    private EditText mkInput(String hint, String value, boolean codeStyle) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setText(value);
        e.setSingleLine(true);
        e.setTextColor(C_TEXT);
        e.setHintTextColor(C_SUB);
        e.setTextSize(codeStyle ? 18 : 16);
        e.setPadding(dp(14), dp(12), dp(14), dp(12));
        e.setBackground(inputBg());
        e.setMinHeight(dp(50));
        // 高亮底框 + 明显的光标，深浅色背景下都能看出这是输入区
        e.setSelectAllOnFocus(false);

        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        p.topMargin = dp(6);
        e.setLayoutParams(p);

        if (codeStyle) {
            // 配对码只有 A-Z 与 2-9：强制大写、关掉输入法联想、过滤杂字符，
            // 否则中文输入法会把「配对码」三个字带进框里，长度永远凑不满 16 位。
            e.setTypeface(android.graphics.Typeface.MONOSPACE);
            e.setLetterSpacing(0.06f);
            e.setInputType(InputType.TYPE_CLASS_TEXT
                    | InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS
                    | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
            e.setFilters(new InputFilter[]{
                    new InputFilter.AllCaps(),
                    new InputFilter() {
                        public CharSequence filter(CharSequence src, int st, int en,
                                                   android.text.Spanned dst, int ds, int de) {
                            StringBuilder sb = new StringBuilder();
                            for (int i = st; i < en; i++) {
                                char c = src.charAt(i);
                                if (Codec.ALPHABET.indexOf(c) >= 0 || c == '-') {
                                    sb.append(c);
                                }
                            }
                            return sb.length() == en - st ? null : sb;
                        }
                    }});
        } else {
            // 地址栏：用 URI 键盘变体，不要自动纠错和首字母大写
            e.setInputType(InputType.TYPE_CLASS_TEXT
                    | InputType.TYPE_TEXT_VARIATION_URI
                    | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        }
        return e;
    }

    /** 白底 + 1dp 边线 + 圆角：浅灰背景上也能一眼看出边界。 */
    private GradientDrawable inputBg() {
        GradientDrawable g = new GradientDrawable();
        g.setShape(GradientDrawable.RECTANGLE);
        g.setColor(C_CARD);
        g.setCornerRadius(dp(8));
        g.setStroke(dp(1), C_LINE);
        return g;
    }

    private Button bigButton(String text, int color) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setTextSize(16);
        b.setBackgroundColor(color);
        b.setAllCaps(false);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(50));
        p.topMargin = dp(6);
        b.setLayoutParams(p);
        return b;
    }

    private String versionName() {
        try {
            return getPackageManager().getPackageInfo(getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "?";
        }
    }

    private void toast(String s) {
        Toast.makeText(this, s, Toast.LENGTH_SHORT).show();
    }

    // ---------------------------------------------------------------- 发现

    private void doDiscover() {
        devList.removeAllViews();
        tvTip.setText("正在搜索…");
        new Thread(new Runnable() {
            public void run() {
                final Map<String, String[]> found = new LinkedHashMap<String, String[]>();
                DatagramSocket sk = null;
                try {
                    sk = new DatagramSocket();
                    sk.setBroadcast(true);
                    sk.setSoTimeout(350);
                    byte[] probe = PROBE.getBytes("UTF-8");
                    DatagramPacket out = new DatagramPacket(probe, probe.length,
                            InetAddress.getByName("255.255.255.255"), DISCOVERY_PORT);
                    for (int i = 0; i < 3; i++) {
                        try {
                            sk.send(out);
                        } catch (Exception ignored) {
                        }
                        try {
                            Thread.sleep(60);
                        } catch (InterruptedException ignored) {
                        }
                    }
                    long end = System.currentTimeMillis() + 1600;
                    byte[] buf = new byte[2048];
                    while (System.currentTimeMillis() < end) {
                        DatagramPacket in = new DatagramPacket(buf, buf.length);
                        try {
                            sk.receive(in);
                        } catch (Exception e) {
                            break;              // 超时：这一轮听完了
                        }
                        String txt = new String(in.getData(), 0, in.getLength(), "UTF-8");
                        if (!txt.startsWith(OFFER)) {
                            continue;
                        }
                        try {
                            JSONObject o = new JSONObject(txt.substring(OFFER.length()));
                            String ip = in.getAddress().getHostAddress();
                            String name = o.optString("name", "电脑");
                            int wp = o.optInt("web", 0);
                            found.put(ip, new String[]{name, ip, String.valueOf(wp)});
                        } catch (Exception ignored) {
                        }
                    }
                } catch (Exception e) {
                    final String m = e.getMessage();
                    ui.post(new Runnable() {
                        public void run() {
                            tvTip.setText("搜索失败：" + m + "\n可以直接在下面填电脑地址。");
                        }
                    });
                    return;
                } finally {
                    if (sk != null) {
                        sk.close();
                    }
                }

                ui.post(new Runnable() {
                    public void run() {
                        showDevices(found);
                    }
                });
            }
        }).start();
    }

    private void showDevices(Map<String, String[]> found) {
        devList.removeAllViews();
        if (found.isEmpty()) {
            tvTip.setText("没搜到。检查两点：手机和电脑连的是同一个路由器；"
                    + "电脑上 LanSplice 是开着的（新版会自动开启手机接入）。"
                    + "\n如果路由器开了「AP 隔离」，广播收不到，请在下面直接填电脑地址。");
            return;
        }
        tvTip.setText("找到 " + found.size() + " 台，点一下连接：");
        for (String[] row : found.values()) {
            final String name = row[0];
            final String ip = row[1];
            final int wp = Integer.parseInt(row[2]);
            Button b = bigButton(name + "  ·  " + ip, C_GRAY);
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, dp(46));
            p.topMargin = dp(8);
            b.setLayoutParams(p);
            b.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    if (wp <= 0) {
                        // 广播里没有网页端口 = 对方是 1.9 之前的版本，没有常驻手机接入
                        toast("这台电脑版本较旧，没开手机接入，先在电脑上点「工具 → 手机传文件」");
                    }
                    connectTo(ip, wp > 0 ? wp : DEFAULT_WEB_PORT, name);
                }
            });
            devList.addView(b);
        }
    }

    // ---------------------------------------------------------------- 连接

    private void connectTo(String ip, int port, String name) {
        String code = edCode.getText().toString();
        String tk;
        try {
            tk = Codec.tokenFor(code);
        } catch (Exception e) {
            // 绝大多数失败是「还没填配对码」。这时候如果只弹一句「配对码要 16 位」，
            // 用户不知道自己刚才哪一步没做——所以直接把光标送回那个框里。
            String m = e.getMessage() == null ? "配对码不对" : e.getMessage();
            toast(code.trim().length() == 0
                    ? "先在上面填 16 位配对码（电脑主界面上「本机配对码」）"
                    : m);
            try {
                edCode.requestFocus();
                pageSetup.smoothScrollTo(0, 0);
            } catch (Exception ignored) {
            }
            return;
        }
        host = ip;
        webPort = port;
        token = tk;
        pcName = name == null ? "" : name;
        sp.edit().putString("code", code.trim().toUpperCase())
                .putString("host", ip).apply();

        // 把手机当前的深浅色直接告诉网页：WebView 里的 prefers-color-scheme
        // 在部分机型上跟系统对不上，显式带一个参数最稳，也能让「手动选深色」
        // 立刻反映到网页上。
        String url = "http://" + ip + ":" + port + "/?t=" + tk
                + "&dark=" + (isDark() ? "1" : "0");
        if (errView != null) {
            errView.setVisibility(View.GONE);
        }
        pageSetup.setVisibility(View.GONE);
        pageWeb.setVisibility(View.VISIBLE);
        web.loadUrl(url);
        if (pending.size() > 0) {
            // 页面加载完再发，因为要先让电脑端把网页服务认下这个连接
            tvOverlay.setVisibility(View.VISIBLE);
            tvOverlay.setText("正在发送上次选的文件…");
        }
    }

    /**
     * 下载电脑发来的文件。
     *
     * 两条路：
     *   · 没选过目录 → 交给系统下载管理器，通知栏有进度、下完点一下就能打开；
     *   · 选过目录   → DownloadManager 写不了 SAF 目录（它只认自己认识的那几个
     *     公共目录），所以自己边收边写进用户指定的位置。
     */
    private void startDownload(String url, String mime) {
        String name = "lansplice-file";
        try {
            String q = Uri.parse(url).getQueryParameter("name");
            if (q != null && q.trim().length() > 0) {
                name = q.trim();
            }
        } catch (Exception ignored) {
        }
        String tree = sp.getString("recv_tree", "");
        if (recvTreeUsable(tree)) {
            downloadToTree(url, mime, name, tree);
            return;
        }
        if (tree.length() > 0) {
            // 目录被删了 / 权限被系统收回了：悄悄退回默认，别让下载失败
            sp.edit().remove("recv_tree").apply();
            refreshSettings();
        }
        DownloadManager dm = (DownloadManager) getSystemService(DOWNLOAD_SERVICE);
        if (dm == null) {
            toast("系统下载器不可用");
            return;
        }
        try {
            DownloadManager.Request r = new DownloadManager.Request(Uri.parse(url));
            r.setTitle(name);
            r.setDescription("来自电脑 · LanSplice");
            r.setNotificationVisibility(
                    DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            if (!TextUtils.isEmpty(mime)) {
                r.setMimeType(mime);
            }
            if (Build.VERSION.SDK_INT >= 29) {
                r.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name);
            } else {
                // Android 9 及以下写公共「下载」目录要存储权限。为了不因此多要一个
                // 权限，旧系统落到应用自己的目录；下完点通知照样能打开。
                r.setDestinationInExternalFilesDir(MainActivity.this,
                        Environment.DIRECTORY_DOWNLOADS, name);
            }
            dm.enqueue(r);
            toast("开始下载：" + name);
        } catch (Exception e) {
            toast("下载失败：" + (e.getMessage() == null ? "未知原因" : e.getMessage()));
        }
    }

    /** 自己收到用户选的目录里。没有进度条通知，就把进度放在底部那条浮层上。 */
    private void downloadToTree(final String url, final String mime,
                                final String name, final String tree) {
        tvOverlay.setVisibility(View.VISIBLE);
        tvOverlay.setText("正在下载：" + name);
        new Thread(new Runnable() {
            public void run() {
                Uri doc = null;
                String err = "";
                long got = 0;
                InputStream in = null;
                OutputStream out = null;
                HttpURLConnection c = null;
                try {
                    Uri t = Uri.parse(tree);
                    Uri dir = DocumentsContract.buildDocumentUriUsingTree(
                            t, DocumentsContract.getTreeDocumentId(t));
                    String mt = TextUtils.isEmpty(mime) ? "application/octet-stream" : mime;
                    // 同名再下一次时，系统会自动存成「xxx (1).xxx」而不是覆盖
                    doc = DocumentsContract.createDocument(getContentResolver(), dir, mt, name);
                    if (doc == null) {
                        throw new Exception("这个目录写不进去");
                    }
                    c = (HttpURLConnection) new URL(url).openConnection();
                    c.setConnectTimeout(8000);
                    c.setReadTimeout(300000);
                    if (c.getResponseCode() != 200) {
                        throw new Exception("电脑端返回 " + c.getResponseCode());
                    }
                    long total = c.getContentLength();
                    in = c.getInputStream();
                    out = getContentResolver().openOutputStream(doc);
                    if (out == null) {
                        throw new Exception("打不开目标文件");
                    }
                    byte[] buf = new byte[64 * 1024];
                    long last = 0;
                    while (true) {
                        int n = in.read(buf);
                        if (n <= 0) {
                            break;
                        }
                        out.write(buf, 0, n);
                        got += n;
                        long now = System.currentTimeMillis();
                        if (now - last > 400) {
                            last = now;
                            final String msg = total > 0
                                    ? "正在下载 " + (got * 100 / total) + "%  "
                                    + sizeText(got) + " / " + sizeText(total)
                                    : "正在下载 " + sizeText(got);
                            ui.post(new Runnable() {
                                public void run() {
                                    tvOverlay.setText(msg);
                                }
                            });
                        }
                    }
                    out.flush();
                } catch (Exception e) {
                    err = e.getMessage() == null ? "未知原因" : e.getMessage();
                } finally {
                    closeQuietly(in);
                    closeQuietly(out);
                    if (c != null) {
                        c.disconnect();
                    }
                }
                // 半截文件比没有文件更糟：失败就把占位文件删掉
                if (err.length() > 0 && doc != null) {
                    try {
                        DocumentsContract.deleteDocument(getContentResolver(), doc);
                    } catch (Exception ignored) {
                    }
                }
                final String ferr = err;
                final long fgot = got;
                ui.post(new Runnable() {
                    public void run() {
                        if (ferr.length() > 0) {
                            tvOverlay.setText("下载失败：" + ferr);
                            tvOverlay.postDelayed(new Runnable() {
                                public void run() {
                                    tvOverlay.setVisibility(View.GONE);
                                }
                            }, 6000);
                        } else {
                            tvOverlay.setText("已存到「"
                                    + recvDirLabel().replace("（点这里改）", "")
                                    + "」：" + name + "  " + sizeText(fgot));
                            tvOverlay.postDelayed(new Runnable() {
                                public void run() {
                                    tvOverlay.setVisibility(View.GONE);
                                }
                            }, 3500);
                        }
                    }
                });
            }
        }).start();
    }

    private static void closeQuietly(java.io.Closeable c) {
        if (c != null) {
            try {
                c.close();
            } catch (Exception ignored) {
            }
        }
    }

    private static String sizeText(long b) {
        if (b < 1024) {
            return b + " B";
        }
        if (b < 1024 * 1024) {
            return String.format("%.0f KB", b / 1024.0);
        }
        if (b < 1024L * 1024 * 1024) {
            return String.format("%.1f MB", b / 1048576.0);
        }
        return String.format("%.2f GB", b / 1073741824.0);
    }

    private boolean sameHost(String url) {
        if (url == null) {
            return true;
        }
        String p = "http://" + host + ":" + webPort;
        return url.startsWith(p) || url.startsWith("about:");
    }

    private void showWebError(String head, String detail) {
        if (errView == null) {
            return;
        }
        errView.setText(head + "\n\n" + detail + "\n\n—— 点这里返回，重新填地址或配对码");
        errView.setVisibility(View.VISIBLE);
        if (tvOverlay != null) {
            tvOverlay.setVisibility(View.GONE);
        }
    }

    private void backToSetup() {
        if (errView != null) {
            errView.setVisibility(View.GONE);
        }
        pageWeb.setVisibility(View.GONE);
        pageSetup.setVisibility(View.VISIBLE);
        try {
            web.stopLoading();
        } catch (Exception ignored) {
        }
    }

    // ---------------------------------------------------------------- 分享进来的文件

    private void handleIntent(Intent it) {
        if (it == null) {
            return;
        }
        String act = it.getAction();
        if (!Intent.ACTION_SEND.equals(act) && !Intent.ACTION_SEND_MULTIPLE.equals(act)) {
            return;
        }
        ArrayList<Uri> list = new ArrayList<Uri>();
        if (Intent.ACTION_SEND.equals(act)) {
            Uri u = (Uri) it.getParcelableExtra(Intent.EXTRA_STREAM);
            if (u != null) {
                list.add(u);
            }
        } else {
            ArrayList<Uri> arr = it.getParcelableArrayListExtra(Intent.EXTRA_STREAM);
            if (arr != null) {
                list.addAll(arr);
            }
        }
        if (list.isEmpty()) {
            // 有些应用只给文字，不给流
            String text = it.getStringExtra(Intent.EXTRA_TEXT);
            if (!TextUtils.isEmpty(text)) {
                toast("这个分享只带了文字，请在网页里发送");
            }
            return;
        }
        pending.clear();
        pending.addAll(list);

        if (token.length() > 0) {
            // 已经连过：直接进网页页并发出去
            pageSetup.setVisibility(View.GONE);
            pageWeb.setVisibility(View.VISIBLE);
            tvOverlay.setVisibility(View.VISIBLE);
            tvOverlay.setText("准备发送 " + pending.size() + " 个文件…");
            if (web.getUrl() == null || !sameHost(web.getUrl())) {
                connectTo(host, webPort, pcName);
            } else {
                sendPending();
            }
        } else {
            // 还没连过：预填上次的配对码，能直接连就直接连，接上后自动发送
            tvTip.setText("收到 " + pending.size() + " 个文件，先连接电脑，接上就自动发送。");
            String lastHost = sp.getString("host", "");
            if (lastHost.length() > 0 && edCode.getText().toString().trim().length() >= 16) {
                connectTo(lastHost, DEFAULT_WEB_PORT, "");
            }
        }
    }

    private void sendPending() {
        if (pending.isEmpty() || token.length() == 0 || host.length() == 0) {
            return;
        }
        final ArrayList<Uri> batch = new ArrayList<Uri>(pending);
        pending.clear();
        tvOverlay.setVisibility(View.VISIBLE);
        new Thread(new Runnable() {
            public void run() {
                int ok = 0;
                String err = "";
                for (int i = 0; i < batch.size(); i++) {
                    final Uri u = batch.get(i);
                    final String nm = displayName(u);
                    final int idx = i;
                    ui.post(new Runnable() {
                        public void run() {
                            tvOverlay.setText("正在发送 " + (idx + 1) + "/" + batch.size()
                                    + "：" + nm);
                        }
                    });
                    try {
                        upload(u, nm);
                        ok++;
                    } catch (Exception e) {
                        err = nm + "：" + e.getMessage();
                    }
                }
                final int fok = ok;
                final String ferr = err;
                ui.post(new Runnable() {
                    public void run() {
                        if (ferr.length() > 0) {
                            tvOverlay.setText("发送完成 " + fok + "/" + batch.size()
                                    + "，有一个失败：" + ferr);
                            tvOverlay.postDelayed(new Runnable() {
                                public void run() {
                                    tvOverlay.setVisibility(View.GONE);
                                }
                            }, 6000);
                        } else {
                            tvOverlay.setText("已发送 " + fok + " 个文件到电脑");
                            tvOverlay.postDelayed(new Runnable() {
                                public void run() {
                                    tvOverlay.setVisibility(View.GONE);
                                }
                            }, 2500);
                        }
                        try {
                            web.reload();       // 刷新电脑上的文件列表
                        } catch (Exception ignored) {
                        }
                    }
                });
            }
        }).start();
    }

    private void upload(Uri u, String name) throws Exception {
        long size = sizeOf(u);
        File tmp = null;
        InputStream in;
        if (size > 0) {
            in = getContentResolver().openInputStream(u);
        } else {
            // 拿不到长度就没法用固定长度模式，电脑端要求 Content-Length，
            // 所以先落到缓存目录问出大小。只有少数流式 provider 会走到这里。
            tmp = new File(getCacheDir(), "up_" + System.currentTimeMillis());
            FileOutputStream fo = new FileOutputStream(tmp);
            InputStream src = getContentResolver().openInputStream(u);
            copy(src, fo, -1);
            src.close();
            fo.close();
            size = tmp.length();
            in = new FileInputStream(tmp);
        }
        if (in == null) {
            throw new Exception("读不到这个文件");
        }
        String url = "http://" + host + ":" + webPort + "/up?t=" + token
                + "&name=" + URLEncoder.encode(name, "UTF-8");
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setRequestMethod("POST");
        c.setDoOutput(true);
        c.setConnectTimeout(8000);
        c.setReadTimeout(300000);
        c.setFixedLengthStreamingMode(size);
        c.setRequestProperty("Content-Type", "application/octet-stream");
        OutputStream os = c.getOutputStream();
        copy(in, os, size);
        os.flush();
        os.close();
        in.close();
        if (tmp != null) {
            tmp.delete();
        }
        int code = c.getResponseCode();
        c.disconnect();
        if (code != 200) {
            throw new Exception("电脑端返回 " + code);
        }
    }

    private static void copy(InputStream in, OutputStream out, long limit) throws Exception {
        byte[] buf = new byte[64 * 1024];
        long done = 0;
        while (true) {
            int n = in.read(buf);
            if (n <= 0) {
                break;
            }
            if (limit > 0 && done + n > limit) {
                n = (int) (limit - done);
            }
            out.write(buf, 0, n);
            done += n;
            if (limit > 0 && done >= limit) {
                break;
            }
        }
    }

    private long sizeOf(Uri u) {
        Cursor c = null;
        try {
            c = getContentResolver().query(u, null, null, null, null);
            if (c != null && c.moveToFirst()) {
                int i = c.getColumnIndex(OpenableColumns.SIZE);
                if (i >= 0 && !c.isNull(i)) {
                    return c.getLong(i);
                }
            }
        } catch (Exception ignored) {
        } finally {
            if (c != null) {
                c.close();
            }
        }
        return -1;
    }

    private String displayName(Uri u) {
        Cursor c = null;
        try {
            c = getContentResolver().query(u, null, null, null, null);
            if (c != null && c.moveToFirst()) {
                int i = c.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (i >= 0 && !c.isNull(i)) {
                    String s = c.getString(i);
                    if (!TextUtils.isEmpty(s)) {
                        return s;
                    }
                }
            }
        } catch (Exception ignored) {
        } finally {
            if (c != null) {
                c.close();
            }
        }
        String p = u.getLastPathSegment();
        return TextUtils.isEmpty(p) ? "file" : p;
    }

    // ---------------------------------------------------------------- 文件选择回传

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req == REQ_DIR) {
            onDirPicked(res, data);
            return;
        }
        if (req != REQ_FILE) {
            return;
        }
        if (filePathCallback == null) {
            return;
        }
        Uri[] out = null;
        if (res == RESULT_OK && data != null) {
            if (data.getClipData() != null) {
                int n = data.getClipData().getItemCount();
                out = new Uri[n];
                for (int i = 0; i < n; i++) {
                    out[i] = data.getClipData().getItemAt(i).getUri();
                }
            } else if (data.getData() != null) {
                out = new Uri[]{data.getData()};
            }
        }
        filePathCallback.onReceiveValue(out);
        filePathCallback = null;
    }

    /**
     * 目录选好了。
     *
     * takePersistableUriPermission 是必须的：不加这句，只有本次运行有效，
     * 用户第二天再打开 App，下载就会往一个「无权限」的目录写，报一堆看不懂的错。
     */
    private void onDirPicked(int res, Intent data) {
        if (res != RESULT_OK || data == null || data.getData() == null) {
            return;
        }
        Uri u = data.getData();
        try {
            getContentResolver().takePersistableUriPermission(u,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION
                            | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        } catch (Exception ignored) {
            // 少数文件管理器不给持久授权，这次仍然能用，只是重启后要重选
        }
        sp.edit().putString("recv_tree", u.toString()).apply();
        refreshSettings();
        String n = recvDirLabel().replace("（点这里改）", "");
        toast("以后电脑发来的文件存到「" + n + "」");
    }

    /** 选中的目录还在不在、能不能写。不在了就该回退到系统下载目录。 */
    private boolean recvTreeUsable(String tree) {
        if (tree == null || tree.length() == 0) {
            return false;
        }
        try {
            Uri t = Uri.parse(tree);
            Uri dir = DocumentsContract.buildDocumentUriUsingTree(
                    t, DocumentsContract.getTreeDocumentId(t));
            Cursor c = getContentResolver().query(dir,
                    new String[]{DocumentsContract.Document.COLUMN_FLAGS,
                            DocumentsContract.Document.COLUMN_MIME_TYPE},
                    null, null, null);
            if (c == null) {
                return false;
            }
            try {
                if (!c.moveToFirst()) {
                    return false;
                }
                String mt = c.getString(1);
                return DocumentsContract.Document.MIME_TYPE_DIR.equals(mt);
            } finally {
                c.close();
            }
        } catch (Exception e) {
            return false;
        }
    }

    // ---------------------------------------------------------------- 返回键

    @Override
    public void onBackPressed() {
        if (errView != null && errView.getVisibility() == View.VISIBLE) {
            backToSetup();
            return;
        }
        if (pageWeb.getVisibility() == View.VISIBLE) {
            if (web.canGoBack()) {
                web.goBack();
                return;
            }
            pageWeb.setVisibility(View.GONE);
            pageSetup.setVisibility(View.VISIBLE);
            return;
        }
        super.onBackPressed();
    }

    // ---------------------------------------------------------------- 崩溃自留证

    private File crashFile() {
        return new File(getFilesDir(), "last_crash.txt");
    }

    private void saveCrash(Throwable t) {
        try {
            StringWriter sw = new StringWriter();
            t.printStackTrace(new PrintWriter(sw));
            FileOutputStream f = new FileOutputStream(crashFile());
            f.write(sw.toString().getBytes("UTF-8"));
            f.close();
        } catch (Throwable ignored) {
        }
    }

    private String readLastCrash() {
        try {
            File f = crashFile();
            if (!f.isFile()) {
                return null;
            }
            byte[] b = new byte[(int) f.length()];
            FileInputStream in = new FileInputStream(f);
            in.read(b);
            in.close();
            f.delete();
            return new String(b, "UTF-8");
        } catch (Throwable e) {
            return null;
        }
    }

    private void showCrashNow(Throwable e) {
        try {
            StringWriter sw = new StringWriter();
            e.printStackTrace(new PrintWriter(sw));
            showText("启动失败：\n\n" + sw.toString(), false);
        } catch (Throwable ignored) {
        }
    }

    private void showText(String msg, final boolean tapToClear) {
        TextView t = new TextView(this);
        t.setText(msg);
        t.setTextColor(C_TEXT);
        t.setTextSize(13);
        t.setBackgroundColor(C_CARD);
        t.setPadding(dp(16), dp(16), dp(16), dp(16));
        if (tapToClear) {
            t.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    if (setupInner != null) {
                        ((LinearLayout) setupInner).removeView(v);
                    }
                }
            });
        }
        if (setupInner instanceof LinearLayout) {
            ((LinearLayout) setupInner).addView(t, 0);
        }
    }
}
