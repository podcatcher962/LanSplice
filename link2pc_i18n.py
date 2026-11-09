# -*- coding: utf-8 -*-
"""
LanSplice 界面文案（中 / 英）
=============================

S[key] = (中文, English)。界面里所有用户可见的文字都从 _t(key) 取，
这样切语言不用改控件结构。key 按抽取顺序编号：g=界面、c=内核。

改文案只改这张表；key 不要动 —— 源码里到处都是 _t("g0xx")。
"""

S = {
    "g001": (
        'LanSplice · 双机直传',
        'LanSplice · Direct PC Transfer',
    ),
    "g002": (
        '© 永远的兰兰',
        '© Lanlan Eternal',
    ),
    "g003": (
        'LanSplice-收件',
        'LanSplice-Inbox',
    ),
    "g004": (
        '<1 秒',
        '<1 s',
    ),
    "g005": (
        '%d 秒',
        '%d s',
    ),
    "g006": (
        '%d 分 %d 秒',
        '%dm %ds',
    ),
    "g007": (
        '%d 小时',
        '%d h',
    ),
    "g008": (
        '添加文件…',
        'Add files…',
    ),
    "g009": (
        '添加文件夹…',
        'Add folder…',
    ),
    "g010": (
        '发送到对端',
        'Send to peer',
    ),
    "g011": (
        '从对端取回…',
        'Fetch from peer…',
    ),
    "g012": (
        '上次传输结果…',
        'Last transfer result…',
    ),
    "g013": (
        '退出',
        'Exit',
    ),
    "g014": (
        '文件',
        'File',
    ),
    "g015": (
        '重新查找设备',
        'Find devices again',
    ),
    "g016": (
        '手动填写对端地址…',
        'Enter peer address…',
    ),
    "g017": (
        '本机网络详情…',
        'My network details…',
    ),
    "g018": (
        '网络体检…',
        'Network checkup…',
    ),
    "g019": (
        '打开接收目录',
        'Open receive folder',
    ),
    "g020": (
        '清空待发清单',
        'Clear queue',
    ),
    "g021": (
        '接收端开关',
        'Receiver on/off',
    ),
    "g022": (
        '工具',
        'Tools',
    ),
    "g023": (
        '查看本机配对码…',
        'Show my pairing code…',
    ),
    "g024": (
        '填写对端配对码…',
        'Enter peer pairing code…',
    ),
    "g025": (
        '重新生成本机配对码…',
        'Regenerate my pairing code…',
    ),
    "g026": (
        '设置接收目录…',
        'Set receive folder…',
    ),
    "g027": (
        '放行防火墙（需管理员）…',
        'Allow in firewall (admin)…',
    ),
    "g028": (
        '安全检查…',
        'Security check…',
    ),
    "g029": (
        '安全',
        'Security',
    ),
    "g030": (
        '使用说明',
        'How to use',
    ),
    "g031": (
        '免责声明',
        'Disclaimer',
    ),
    "g032": (
        '关于',
        'About',
    ),
    "g033": (
        '帮助',
        'Help',
    ),
    "g034": (
        '本机',
        'This PC',
    ),
    "g035": (
        '对端 未连接',
        'Peer  not connected',
    ),
    "g036": (
        '点「工具 → 重新查找设备」',
        'Tools → Find devices again',
    ),
    "g037": (
        '保存到',
        'Save to',
    ),
    "g038": (
        '更改…',
        'Change…',
    ),
    "g039": (
        '打开',
        'Open',
    ),
    "g040": (
        '一键放行防火墙',
        'Allow in firewall',
    ),
    "g041": (
        '● 防火墙 检测中…',
        '● Firewall  checking…',
    ),
    "g042": (
        '设备',
        'Devices',
    ),
    "g043": (
        '重新查找',
        'Find again',
    ),
    "g044": (
        '本机配对码',
        'My pairing code',
    ),
    "g045": (
        '复制配对码',
        'Copy code',
    ),
    "g046": (
        '填写对端配对码',
        'Enter peer code',
    ),
    "g047": (
        '把文件或文件夹拖到这里',
        'Drop files or folders here',
    ),
    "g048": (
        '支持多文件、多文件夹；资源管理器里复制后，回到这里按 Ctrl+V 也行',
        'Multiple files and folders. You can also copy them in Explorer and press Ctrl+V here.',
    ),
    "g049": (
        '拖拽不可用：用下方按钮，或复制文件后回来按 Ctrl+V',
        'Drag & drop unavailable — use the buttons below, or copy files and press Ctrl+V.',
    ),
    "g050": (
        '选择文件…',
        'Choose files…',
    ),
    "g051": (
        '选择文件夹…',
        'Choose folder…',
    ),
    "g052": (
        '清空',
        'Clear',
    ),
    "g053": (
        '拖拽组件没装好，请用下方按钮选择文件',
        "Drag & drop isn't available. Please use the buttons below.",
    ),
    "g054": (
        '待发清单',
        'Queue',
    ),
    "g055": (
        '空',
        'Empty',
    ),
    "g056": (
        '清空全部',
        'Clear all',
    ),
    "g057": (
        '移除选中',
        'Remove',
    ),
    "g058": (
        'Ctrl+V 或右键粘贴 · Delete 移除',
        'Ctrl+V / right-click to paste · Del to remove',
    ),
    "g059": (
        '大小',
        'Size',
    ),
    "g060": (
        '进度',
        'Progress',
    ),
    "g061": (
        '速度',
        'Speed',
    ),
    "g062": (
        '状态',
        'Status',
    ),
    "g063": (
        '①  发送到对端',
        '①  Send to peer',
    ),
    "g064": (
        '②  从对端取回',
        '②  Fetch from peer',
    ),
    "g065": (
        '停止',
        'Stop',
    ),
    "g066": (
        '详情',
        'Details',
    ),
    "g067": (
        '就绪',
        'Ready',
    ),
    "g068": (
        '本机  %s',
        'This PC  %s',
    ),
    "g069": (
        '未取到地址',
        'No address',
    ),
    "g070": (
        '%s  等 %d 个地址',
        '%s  and %d more',
    ),
    "g071": (
        'AES-256-GCM · 已加密',
        'AES-256-GCM · encrypted',
    ),
    "g072": (
        '接收端已关闭',
        'Receiver off',
    ),
    "g073": (
        '· 接收端口 %d',
        '· port %d',
    ),
    "g074": (
        '接收端口 %d\n对端发来的文件存到上面的目录',
        'Receive port %d\nFiles land in the folder above',
    ),
    "g075": (
        '%d 项 · %d 个文件 · %s',
        '%d items · %d files · %s',
    ),
    "g076": (
        '对端  %s',
        'Peer  %s',
    ),
    "g077": (
        '对端  未连接',
        'Peer  not connected',
    ),
    "g078": (
        '查找中…',
        'Searching…',
    ),
    "g079": (
        '（没找到电脑，点下面「手动填写对端地址」）',
        "(no PC found — enter the peer address below)",
    ),
    "g080": (
        '没有找到电脑：检查对端软件开了没；手机请点列表里的「手机」',
        'No PC found — check the peer has the app open; for a phone use "Phone" below',
    ),
    "g081": (
        '找到 %d 台设备',
        '%d device(s) found',
    ),
    "g082": (
        '（',
        '(',
    ),
    "g083": (
        '发现 %s（%s）',
        'Found %s (%s)',
    ),
    "g084": (
        '手动填写对端地址',
        'Enter peer address',
    ),
    "g085": (
        '填对端 IP，端口默认 %d。\n不确定是哪个就一次填多个，用空格或逗号隔开，程序逐个试。',
        'Peer IP; port defaults to %d.\nNot sure which one? Enter several separated by spaces or commas and each will be tried.',
    ),
    "g086": (
        '，',
        ', ',
    ),
    "g087": (
        '正在逐个试 %d 个地址…',
        'Trying %d addresses…',
    ),
    "g088": (
        '正在试 %d 个候选地址…',
        'Trying %d candidate addresses…',
    ),
    "g089": (
        '%s 不通（%s）',
        '%s unreachable (%s)',
    ),
    "g090": (
        '；',
        '; ',
    ),
    "g091": (
        '  %-15s /%-2d   广播 %-15s %s',
        '  %-15s /%-2d   bcast %-15s %s',
    ),
    "g092": (
        '  （没取到网卡信息）',
        '  (no adapter info)',
    ),
    "g093": (
        '主机名：%s\n\n本机地址：\n%s\n\n两台机器要互传，必须各有一条「同网段」的地址。\n192.168.56.x / 192.168.51.x / 172.17.x 这类基本是\n虚拟机、Hyper-V 或 VPN 的虚拟网卡，只有本机内部存在，\n对端连不上，发现广播也到不了那里。\n\n如果在列表里看到 192.168.0.x（或你家路由器那个网段），\n就用那条地址。',
        "Host name: %s\n\nAddresses on this PC:\n%s\n\nBoth machines need an address on the 'same subnet'.\n192.168.56.x / 192.168.51.x / 172.17.x are usually virtual\nadapters from a VM, Hyper-V or a VPN — they only exist inside\nthis machine, so the peer can neither reach them nor hear the\ndiscovery broadcast there.\n\nIf you see a 192.168.0.x address (or whatever your router uses),\nthat's the one to use.",
    ),
    "g094": (
        '本机网络详情',
        'My network details',
    ),
    "g095": (
        '还没有选择对端设备，点窗口左边的「重新查找」。',
        'No peer selected yet — click "Find devices again" on the left.',
    ),
    "g096": (
        '正在验证…',
        'Verifying…',
    ),
    "g097": (
        '正在传输，先点「停止」再粘贴',
        'A transfer is running — click Stop before pasting',
    ),
    "g098": (
        '剪贴板里没有文件（先在资源管理器里选中文件按 Ctrl+C）',
        'No files on the clipboard (select files in Explorer and press Ctrl+C first)',
    ),
    "g099": (
        '这 %d 项已经在清单里，或者已经找不到了',
        'These %d items are already in the queue, or no longer exist',
    ),
    "g100": (
        '粘贴（Ctrl+V）',
        'Paste (Ctrl+V)',
    ),
    "g101": (
        '选择要发送的文件',
        'Choose files to send',
    ),
    "g102": (
        '选择要发送的文件夹',
        'Choose a folder to send',
    ),
    "g103": (
        '正在添加 %d 项…',
        'Adding %d items…',
    ),
    "g104": (
        ' / %d个',
        ' / %d files',
    ),
    "g105": (
        '待发送',
        'Queued',
    ),
    "g106": (
        '已添加 %d 项',
        'Added %d item(s)',
    ),
    "g107": (
        '正在传输，先点「停止」。',
        'A transfer is running — click Stop first.',
    ),
    "g108": (
        '清单是空的，先拖文件进来。',
        'The queue is empty — drop some files in first.',
    ),
    "g109": (
        '还没有选择对端设备，点窗口左边的「重新查找」。',
        'No peer selected yet — click "Find devices again" on the left.',
    ),
    "g110": (
        '等待',
        'Waiting',
    ),
    "g111": (
        '配对码不匹配：两台机器的码必须一样。',
        'Pairing code mismatch: both machines must use the same code.',
    ),
    "g112": (
        '连不上对端：%s',
        "Can't reach the peer: %s",
    ),
    "g113": (
        '已连接 %s，开始传输',
        'Connected to %s, starting transfer',
    ),
    "g114": (
        '已是最新，跳过',
        'Already up to date, skipped',
    ),
    "g115": (
        '完成',
        'Done',
    ),
    "g116": (
        '已取消',
        'Cancelled',
    ),
    "g117": (
        '失败',
        'Failed',
    ),
    "g118": (
        '已发送 %d 项 → %s · %s · %.0f 秒 · %.0f MB/s',
        'Sent %d items → %s · %s · %.0f s · %.0f MB/s',
    ),
    "g119": (
        '  ·  存到 %s',
        '  ·  saved to %s',
    ),
    "g120": (
        '  ·  %d 个已是最新（跳过）',
        '  ·  %d already up to date (skipped)',
    ),
    "g121": (
        '%s · %d 个失败（点「详情」看原因）',
        '%s · %d failed (see Details)',
    ),
    "g122": (
        '%s：%s',
        '%s: %s',
    ),
    "g123": (
        '\n\n失败明细：\n',
        '\n\nFailures:\n',
    ),
    "g124": (
        '\n\n失败的条目会留在待发清单里，可以直接重发。',
        '\n\nFailed items stay in the queue so you can send them again.',
    ),
    "g125": (
        '空（已发送的已自动移出）',
        'Empty (sent items were removed)',
    ),
    "g126": (
        '还没有传输记录，先发一次文件。',
        'No transfers yet — send something first.',
    ),
    "g127": (
        '对端\u3000\u3000：%s（%s）',
        'Peer     : %s (%s)',
    ),
    "g128": (
        '接收目录：%s',
        'Folder   : %s',
    ),
    "g129": (
        '（对端未上报）',
        '(not reported by the peer)',
    ),
    "g130": (
        '完成时间：%s',
        'Finished : %s',
    ),
    "g131": (
        '共 %d 项 · %s · 用时 %.1f 秒 · 平均 %.1f MB/s',
        '%d items · %s · %.1f s · avg %.1f MB/s',
    ),
    "g132": (
        '发送清单',
        'Sent items',
    ),
    "g133": (
        '其中 %d 个文件对端已是最新，跳过了。',
        '%d files were already up to date on the peer and got skipped.',
    ),
    "g134": (
        '在对端的位置',
        'On the peer machine',
    ),
    "g135": (
        '（点下方「在对端打开文件夹」，会在对端电脑上直接弹出这个目录）',
        "(Click 'Open on peer' below to pop this folder open on the other machine)",
    ),
    "g136": (
        '    （整个文件夹）',
        '    (whole folder)',
    ),
    "g137": (
        '失败 %d 个',
        '%d failed',
    ),
    "g138": (
        '  %s：%s',
        '  %s: %s',
    ),
    "g139": (
        '全部成功，没有失败项。',
        'All succeeded, nothing failed.',
    ),
    "g140": (
        '传输结果',
        'Transfer result',
    ),
    "g141": (
        '结果已复制到剪贴板',
        'Result copied to the clipboard',
    ),
    "g142": (
        '关闭',
        'Close',
    ),
    "g143": (
        '复制全部',
        'Copy all',
    ),
    "g144": (
        '在对端打开文件夹',
        'Open on peer',
    ),
    "g145": (
        '对端地址未知，先重新查找设备再试。',
        'Peer address unknown — search for devices again first.',
    ),
    "g146": (
        '正在请 %s 打开文件夹…',
        'Asking %s to open the folder…',
    ),
    "g147": (
        '防火墙 已放行',
        'Firewall  allowed',
    ),
    "g148": (
        '（公用网络）',
        '(public network)',
    ),
    "g149": (
        '防火墙 未放行，点右侧按钮',
        'Firewall  blocked — use the button on the right',
    ),
    "g150": (
        '防火墙 状态未知',
        'Firewall  unknown',
    ),
    "g151": (
        '正在停止…',
        'Stopping…',
    ),
    "g152": (
        '从对端取回',
        'Fetch from peer',
    ),
    "g153": (
        '输入对端接收目录下的相对路径，例如：城市声音志\\北京',
        "Enter a path relative to the peer's receive folder, e.g. Albums\\Beijing",
    ),
    "g154": (
        '正在向对端查询…',
        'Asking the peer…',
    ),
    "g155": (
        '对端没有：%s',
        'Not found on the peer: %s',
    ),
    "g156": (
        '「%s」是个文件夹。\n\n单文件取回请填到具体文件名。\n整目录取回建议用「双向」或直接在聊天里告诉我。',
        "'%s' is a folder.\n\nEnter a specific file name to fetch a single file.",
    ),
    "g157": (
        '存到哪里',
        'Save to',
    ),
    "g158": (
        '接收端按设置未启动，可在「工具」里手动开',
        'Receiver is off (disabled in settings); turn it on under Tools',
    ),
    "g159": (
        '接收目录建不了：%s',
        "Can't create the receive folder: %s",
    ),
    "g160": (
        '已被使用',
        'already in use',
    ),
    "g161": (
        '只允许使用一次',
        'only one use allowed',
    ),
    "g162": (
        '端口 %d 被占用，%d 秒后自动重试（第 %d 次）…',
        'Port %d is in use; retrying in %d s (attempt %d)…',
    ),
    "g163": (
        '接收端启动失败：%s\n\n%s',
        'Receiver failed to start: %s\n\n%s',
    ),
    "g164": (
        '可能还有另一个窗口开着（旧版本，或者图标点了两次）。\n\n在任务栏或右下角托盘区（点 ^ 展开）找到它，右键「退出 LanSplice」。\n关闭时选「彻底退出」；选「最小化到托盘」端口还占着。\n\n再点「工具 → 接收端开关」重新打开。',
        "Another copy may still be running (an older version, or a double-click on the icon).\n\nFind it on the taskbar or in the notification area (click ^ to expand), right-click it and choose \"Quit LanSplice\".\nWhen closing, pick \"Quit completely\" — \"Minimise to tray\" keeps the port taken.\n\nThen use Tools → Receiver on/off to start it again.",
    ),
    "g165": (
        '可能是防火墙拦截，可到「安全 → 放行防火墙」处理。',
        'The firewall may be blocking it — see Security → Allow in firewall.',
    ),
    "g166": (
        '接收端已开启',
        'Receiver on',
    ),
    "g167": (
        '本机配对码：\n\n        %s\n\n记下这串码，到对端电脑的窗口左侧点「填写对端配对码」，在输入框里填进去。\n\n反过来也行：把对端的配对码填到本机。两边一致才能配对。\n\n配对码属于密码，别发到群里、别截图外传。',
        "Pairing code for this PC:\n\n        %s\n\nNote it down, then on the other PC click \"Enter peer code\" on the left and type it into the box.\n\nOr the other way round: enter that machine\'s code here. Both sides must match.\n\nTreat it like a password — don't post it in group chats or share screenshots.",
    ),
    "g168": (
        '配对码已复制',
        'Pairing code copied',
    ),
    "g169": (
        '把另一台显示的配对码填进来（形如 ABCD-EFGH-JKLM-NPQR）：',
        'Enter the code shown on the other machine (looks like ABCD-EFGH-JKLM-NPQR):',
    ),
    "g170": (
        '已更新配对码。\n另一台也要填同一串码才能连通。',
        'Pairing code updated.\nThe other machine must use the same code to connect.',
    ),
    "g171": (
        '重新生成会让另一台连不上，需要在那边重新填一次。继续？',
        'Regenerating will cut off the other machine until you enter the new code there. Continue?',
    ),
    "g172": (
        '选接收目录（对端发来的文件存这里）',
        'Choose the receive folder (incoming files are saved here)',
    ),
    "g173": (
        '不能选系统目录。换一个普通文件夹。',
        "That's a system folder. Please pick a normal folder.",
    ),
    "g174": (
        '接收目录已改',
        'Receive folder updated',
    ),
    "g175": (
        '检测到本机有网卡被 Windows 归为「公用网络」。\n\n本软件原来只对「专用网络」放行，所以在公用网络下\n端口是关着的——这正是「都在同一网段却连不上」最常见的原因。\n\n建议：把家里的网络改成「专用」。这不会让外网访问到本机，\n只是告诉 Windows「这是我信任的家庭网络」。\n\n要改成专用并重设防火墙规则吗？\n（选「否」则只放宽防火墙，网络类别不动）',
        "Windows has classified one of your network adapters as a 'Public network'.\n\nThis app used to allow traffic only on Private networks, so on a Public\nnetwork the port stays closed — which is the most common reason two machines\non the same subnet still can't see each other.\n\nSuggestion: switch the home network to Private. This does NOT expose this PC\nto the internet — it only tells Windows 'this is my trusted home network'.\n\nSwitch it to Private and rebuild the firewall rules?\n(Choose No to only relax the firewall and leave the network category alone)",
    ),
    "g176": (
        '放行防火墙',
        'Allow in firewall',
    ),
    "g177": (
        '开始重新整理本软件的防火墙规则：\n\n'
        '  1. 删掉本软件以前版本建的规则（LanSplice、Link2PC 开头的都清掉），\n'
        '     包括第一次启动时你点过「允许」、系统按程序路径自动建的那条\n'
        '  2. 重建三条按端口的规则：TCP %d 传文件、UDP %d 内网发现、TCP %d 手机网页\n'
        '  3. 只允许这三个内网地址连进来：192.168.x.x（家里路由器最常见）、\n'
        '     10.x.x.x（公司常见）、172.16~31.x.x。公网地址进不来\n\n'
        '用的是 Windows 自带的 netsh 命令，不写脚本文件、不碰注册表。\n'
        '需要点一次「是」授权（管理员权限）。继续？',
        "This will rebuild the firewall rules for this app:\n\n"
        "  1. Delete the rules older versions left behind (anything named LanSplice* or\n"
        "     Link2PC*), including the one Windows created by program path when you\n"
        "     clicked Allow on first launch\n"
        "  2. Create three rules by port: TCP %d for file transfer, UDP %d for LAN discovery,\n"
        "     and TCP %d for the phone web page (the Android APK loads that page too)\n"
        "  3. Allow only these private ranges in: 192.168.x.x (most home routers),\n"
        "     10.x.x.x (common at work), 172.16-31.x.x. Internet addresses can't get in\n\n"
        "Uses the built-in netsh command: no script files, no registry edits.\n"
        "You will get one administrator prompt. Continue?",
    ),
    "g178": (
        '本次同时把公用网络改为专用。',
        'This run also switches public networks to Private.',
    ),
    "g179": (
        '本次不改网络类别；公用网络下可能仍需手动改专用。',
        'The network category is left unchanged; on a public network you may still need to switch it to Private.',
    ),
    "g180": (
        '放行失败：%s',
        'Failed: %s',
    ),
    "g181": (
        '正在重启接收端，让新规则生效…',
        'Restarting the receiver so the new rules take effect…',
    ),
    "g182": (
        '已重设。当前规则 %d 条%s。\n\n%s\n\n验证：另一台点「工具 → 重新查找设备」。',
        'Done. %d rule(s) now%s.\n\n%s\n\nVerify: on the other machine, click Tools → Find devices again.',
    ),
    "g183": (
        '（启用中）',
        ' (enabled)',
    ),
    "g184": (
        '（未生效，多半是没拿到管理员授权）',
        ' (not active — likely no admin approval)',
    ),
    "g185": (
        '接收端已自动重启，新规则立即生效，不用再关程序了。',
        'The receiver restarted automatically, so the new rules apply right away — no need to restart the app.',
    ),
    "g186": (
        '接收端重启失败，请关掉程序重开一次。',
        'The receiver failed to restart. Please close and reopen the app.',
    ),
    "g187": (
        '正在诊断…',
        'Diagnosing…',
    ),
    "g188": (
        '【本机】%s',
        '[This PC] %s',
    ),
    "g189": (
        '【本机】读取失败 %s',
        '[This PC] read failed %s',
    ),
    "g190": (
        '专用',
        'Private',
    ),
    "g191": (
        '公用',
        'Public',
    ),
    "g192": (
        '域',
        'Domain',
    ),
    "g193": (
        '【网络类别】',
        '[Network category]',
    ),
    "g194": (
        '接口%d=%s',
        'iface%d=%s',
    ),
    "g195": (
        '        ! 有「公用」接口，专用规则对它不生效',
        "        ! a Public interface exists, so private-only rules don't apply to it",
    ),
    "g196": (
        '【网络类别】读不到',
        '[Network category] unavailable',
    ),
    "g197": (
        '【网络类别】%s',
        '[Network category] %s',
    ),
    "g198": (
        '【接收端】%s（127.0.0.1:%d）',
        '[Receiver] %s (127.0.0.1:%d)',
    ),
    "g199": (
        '在监听',
        'listening',
    ),
    "g200": (
        '没在监听',
        'not listening',
    ),
    "g201": (
        '【防火墙】%s  启用=%s  作用=%s',
        '[Firewall] %s  enabled=%s  profile=%s',
    ),
    "g202": (
        '【防火墙】没有 LanSplice 规则，点「安全 → 放行防火墙」',
        '[Firewall] no LanSplice rule — use Security → Allow in firewall',
    ),
    "g203": (
        '【防火墙】%s',
        '[Firewall] %s',
    ),
    "g204": (
        '【对端 %s:%d】通',
        '[Peer %s:%d] reachable',
    ),
    "g205": (
        '【对端 %s:%d】被拒，对端软件没在跑',
        "[Peer %s:%d] refused — the app isn't running there",
    ),
    "g206": (
        '【对端 %s:%d】超时无回应，对端防火墙在丢包',
        "[Peer %s:%d] timed out — the peer's firewall is dropping packets",
    ),
    "g207": (
        '【对端 %s:%d】%s',
        '[Peer %s:%d] %s',
    ),
    "g208": (
        '【对端】尚未选择',
        '[Peer] not selected yet',
    ),
    "g209": (
        '连接诊断',
        'Connection diagnosis',
    ),
    "g210": (
        '\n\n—— 要现在自动修复防火墙吗？',
        '\n\n— Fix the firewall automatically now?',
    ),
    "g211": (
        '本机：%s（%s）',
        'This PC: %s (%s)',
    ),
    "g212": (
        '未取到',
        'unavailable',
    ),
    "g213": (
        '接收端：%s，端口 %d',
        'Receiver: %s, port %d',
    ),
    "g214": (
        '运行中',
        'running',
    ),
    "g215": (
        '已关闭',
        'stopped',
    ),
    "g216": (
        '【通道】AES-256-GCM 全帧加密，双向独立密钥',
        '[Channel] every frame is AES-256-GCM encrypted, with separate keys per direction',
    ),
    "g217": (
        '【身份】X25519 密钥交换 + 配对码 HMAC 双向认证',
        '[Identity] X25519 key exchange plus HMAC mutual authentication with the pairing code',
    ),
    "g218": (
        '【来源】只接受内网网段，公网 IPv4/IPv6 一律拒绝',
        '[Source] only private ranges are accepted; public IPv4/IPv6 is rejected outright',
    ),
    "g219": (
        '【写入】只落在接收目录内，路径越界/盘符/保留名全部拦截',
        '[Writes] files can only land inside the receive folder; path traversal, drive letters and reserved names are all blocked',
    ),
    "g220": (
        '【共享】不使用 Windows 共享，445 端口全程关闭',
        '[Sharing] Windows file sharing is not used; port 445 stays closed the whole time',
    ),
    "g221": (
        '【注意】对端发来的 .exe / .bat / .lnk 不要直接双击，',
        "[Care] don't double-click .exe / .bat / .lnk files that arrive from the peer —",
    ),
    "g222": (
        '        先看清是什么再决定。两边是同一个人也建议保留这个习惯。',
        '       check what they are first. Same person on both ends, same habit.',
    ),
    "g223": (
        '安全检查',
        'Security check',
    ),
    "g224": (
        "1. 两台电脑都装好软件，双击打开，窗口左边显示本机配对码。\n"
        "2. 让两台的配对码一样：在一台上点「复制配对码」，\n"
        "   到另一台上点「填写对端配对码」填进去。\n"
        "3. 点窗口左边的「重新查找」。对端也开着软件的话，\n"
        "   列表里会出现它，点一下选中。\n"
        "4. 把要传的文件或文件夹拖进虚线框，\n"
        "   也可以点「选择文件…」「选择文件夹…」。\n"
        "5. 点窗口左下角的「① 发送到对端」。\n"
        "\n"
        "传过去的文件存在对端的接收目录里（默认 E:\\_xfer，没有 E 盘就存在用户目录）。\n"
        "同一个文件再传一次会直接跳过；同名但内容改过的，会另存为「xxx (2)」，不覆盖原文件。\n"
        "\n"
        "第一次用，对端找不到本机：点窗口右下角的「一键放行防火墙」。\n"
        "\n"
        "—— 1.4 新增 ——\n"
        "· 断点续传\n"
        "· 同名不覆盖\n"
        "· 发文字：两台直接推文字，在对端弹出窗口，可以复制\n"
        "· 手机传文件：文件 → 手机传文件，手机扫码就能收发，不用装东西\n"
        "· 关窗口只是缩到托盘，接收不中断；托盘右键可以「开机自动启动」\n"
        "· 设置 → 传完再校验文件：慢一点，但更可靠\n"
        "\n"
        "—— 1.5 新增 ——\n"
        "· 文件夹镜像：工具 → 镜像文件夹…，只补新增和改过的，适合长期同步\n"
        "· 命令行：LanSplice.exe send <路径> --to <IP>，可以写进批处理和计划任务；\n"
        "  另有 devices（扫局域网）和 version",
        "1. Install the app on both PCs and open it — your pairing code is on the left.\n"
        "2. Make the two codes match: click \"Copy code\" on one,\n"
        "   then \"Enter peer code\" on the other and type it in.\n"
        "3. Click \"Find again\" on the left. If the peer has the app open,\n"
        "   it shows up in the list — click to select it.\n"
        "4. Drag files or folders into the dashed box,\n"
        "   or use \"Choose files…\" / \"Choose folder…\".\n"
        "5. Click \"①  Send to peer\" at the bottom left.\n"
        "\n"
        "Files land in the peer's receive folder (E:\\_xfer by default; without an\n"
        "E: drive it goes to your user folder). Sending the same file again is\n"
        "skipped; a same-name file with different content is saved as \"xxx (2)\".\n"
        "\n"
        "If the peer cannot find this PC the first time, click \"Allow in firewall\"\n"
        "at the bottom right.\n"
        "\n"
        "—— New in 1.4 ——\n"
        "· Resume an interrupted transfer\n"
        "· Same-name files are never overwritten\n"
        "· Text: push text straight to the peer; it pops up there and can be copied\n"
        "· Phone transfer: File → Phone transfer — scan the code, nothing to install\n"
        "· Closing the window only hides it to the tray; right-click the tray icon\n"
        "  for \"Start with Windows\"\n"
        "· Settings → Verify the file after transfer: slower, more reliable\n"
        "\n"
        "—— New in 1.5 ——\n"
        "· Folder mirror: Tools → Mirror a folder… — only new and changed files\n"
        "· Command line: LanSplice.exe send <path> --to <IP>, usable in batch files\n"
        "  and scheduled tasks; also devices (scan the LAN) and version",
    ),
    "g225": (
        '本软件用于同一局域网内的两台自有设备之间传输文件。\n\n· 请勿用于传输违法内容。\n· 请妥善保管配对码，配对码泄露等于把接收目录对外开放。\n· 对端发来的可执行文件请自行判断风险，本软件不做病毒扫描。\n· 作者不对使用本软件造成的任何数据损失或法律后果负责。',
        'This app transfers files between two machines you own on the same local network.\n\n· Do not use it to transfer illegal content.\n· Keep the pairing code safe — anyone with the code can write into your receive folder.\n· Judge executable files from the peer yourself; this app does not scan for viruses.\n· The author is not liable for any data loss or legal consequence caused by using this app.',
    ),
    "g226": (
        '%s  v%s\n\n双机局域网直传 · 加密通道 · 免共享\n\n%s\n基于 Python + tkinter + cryptography'
        '\n\nMIT 许可：自由使用、修改、分发，保留版权声明与署名即可'
        '\ngithub.com/podcatcher962/LanSplice',
        '%s  v%s\n\nDirect PC-to-PC transfer on your LAN · encrypted · no file sharing\n\n%s\nBuilt with Python + tkinter + cryptography'
        '\n\nMIT licence: free to use, modify and redistribute — keep the notice and credit'
        '\ngithub.com/podcatcher962/LanSplice',
    ),
    "g227": (
        '已连接 %s，通道已加密',
        'Connected to %s, channel encrypted',
    ),
    "g228": (
        '配对码不一致',
        "Pairing codes don't match",
    ),
    "g229": (
        '连不上：%s',
        "Can't connect: %s",
    ),
    "g230": (
        '收到 %s',
        'Received %s',
    ),
    "g231": (
        '已在 %s 上打开：%s',
        'Opened on %s: %s',
    ),
    "g232": (
        '未知指令',
        'Unknown command',
    ),
    "g233": (
        '对端 LanSplice 版本较旧，不支持远程打开文件夹。\n把两台机器都升级到 v%s 再试。',
        "The peer is running an older LanSplice that can't open folders remotely.\nUpdate both machines to v%s and try again.",
    ),
    "g234": (
        '没能让 %s 打开文件夹：\n\n%s',
        "Couldn't make %s open the folder:\n\n%s",
    ),
    "g235": (
        '连接失败',
        'Connection failed',
    ),
    "g236": (
        '重新放行防火墙',
        'Allow again',
    ),
    "g237": (
        '传输中',
        'Transferring',
    ),
    "g238": (
        '  · 剩 %s',
        '  ·  %s left',
    ),
    "g239": (
        '跳过',
        'Skipped',
    ),
    "g240": (
        '传输中 %d/%d',
        'Transferring %d/%d',
    ),
    "g241": (
        '取回失败：%s',
        'Fetch failed: %s',
    ),
    "g242": (
        '取回完成',
        'Fetch complete',
    ),
    "g243": (
        '正在传输，确定退出？',
        'A transfer is running. Quit anyway?',
    ),
    "g244": (
        '(写日志失败)',
        '(failed to write the log)',
    ),
    "g245": (
        'LanSplice 启动失败',
        'LanSplice failed to start',
    ),
    "g246": (
        '程序没能启动，把下面这段发给我：\n\n',
        "The app couldn't start. Please send me this:\n\n",
    ),
    "g247": (
        '\n\n日志：',
        '\n\nLog: ',
    ),
    "g248": (
        '正在传输，先点「停止」再切换语言',
        'A transfer is running — click Stop before switching language',
    ),
    "c001": (
        '连接已断开',
        'Connection closed',
    ),
    "c002": (
        '常见虚拟机网段',
        'common VM subnet',
    ),
    "c003": (
        'Windows 热点共享',
        'Windows hotspot / ICS',
    ),
    "c004": (
        '常见容器/虚拟机网段',
        'common container/VM subnet',
    ),
    "c005": (
        'GetIpAddrTable 取长度失败',
        'GetIpAddrTable failed to return a size',
    ),
    "c006": (
        'GetIpAddrTable 返回 %d',
        'GetIpAddrTable returned %d',
    ),
    "c007": (
        '配对码应为 16 位（不含横线），当前 %d 位',
        'Pairing code must be 16 characters (dashes ignored); got %d',
    ),
    "c008": (
        '帧长度异常：%d',
        'Bad frame length: %d',
    ),
    "c009": (
        '解密失败（数据被篡改或密钥不匹配）',
        'Decryption failed (tampered data or wrong key)',
    ),
    "c010": (
        '空帧',
        'Empty frame',
    ),
    "c011": (
        '期待控制帧，收到 %r',
        'Expected a control frame, got %r',
    ),
    "c012": (
        '期待数据帧，收到 %r',
        'Expected a data frame, got %r',
    ),
    "c013": (
        '对端不是 LanSplice 服务',
        'The peer is not a LanSplice service',
    ),
    "c014": (
        '配对码不匹配',
        'Pairing code mismatch',
    ),
    "c015": (
        '未知协议',
        'Unknown protocol',
    ),
    "c016": (
        '路径为空',
        'Empty path',
    ),
    "c017": (
        '拒绝绝对路径：%s',
        'Absolute path rejected: %s',
    ),
    "c018": (
        '路径越界：%s',
        'Path escapes the receive folder: %s',
    ),
    "c019": (
        '保留设备名：%s',
        'Reserved device name: %s',
    ),
    "c020": (
        '接收端已启动，端口 %d，接收目录 %s',
        'Receiver started on port %d, folder %s',
    ),
    "c021": (
        '接收端启动失败：%s',
        'Receiver failed to start: %s',
    ),
    "c022": (
        '拒绝来自非局域网的连接：%s',
        'Rejected a non-LAN connection: %s',
    ),
    "c023": (
        '发现服务启动失败（不影响直连）：%s',
        'Discovery service failed to start (direct transfer still works): %s',
    ),
    "c024": (
        '✗ %s 配对码不匹配，已断开',
        '✗ %s wrong pairing code, disconnected',
    ),
    "c025": (
        '✗ %s 握手失败：%s',
        '✗ %s handshake failed: %s',
    ),
    "c026": (
        '✓ %s 已认证，通道已加密',
        '✓ %s authenticated, channel encrypted',
    ),
    "c027": (
        '连接异常（%s）：%s',
        'Connection error (%s): %s',
    ),
    "c028": (
        '· %s 断开',
        '· %s disconnected',
    ),
    "c029": (
        '未知指令 %r',
        'Unknown command %r',
    ),
    "c030": (
        '对端磁盘空间不足',
        'Not enough space on the peer',
    ),
    "c031": (
        '字节数不符：期望 %d，实收 %d',
        'Byte count mismatch: expected %d, got %d',
    ),
    "c032": (
        '← 收到 %s (%s, %.1f MB/s)',
        '← received %s (%s, %.1f MB/s)',
    ),
    "c033": (
        '接收失败 %s：%s',
        'Receive failed %s: %s',
    ),
    "c034": (
        '文件不存在',
        'File not found',
    ),
    "c035": (
        '→ 发出 %s (%s, %.1f MB/s)',
        '→ sent %s (%s, %.1f MB/s)',
    ),
    "c036": (
        '发送失败 %s：%s',
        'Send failed %s: %s',
    ),
    "c037": (
        '接收目录不存在：%s',
        'Receive folder missing: %s',
    ),
    "c038": (
        '打开失败：%s',
        'Failed to open: %s',
    ),
    "c039": (
        '→ 已打开 %s（对端请求）',
        '→ opened %s (peer request)',
    ),
    "c040": (
        '对端响应异常',
        'Unexpected response from the peer',
    ),
    "c041": (
        '对端打开失败',
        'The peer failed to open it',
    ),
    "c042": (
        '对端拒绝接收',
        'The peer refused the transfer',
    ),
    "c043": (
        '用户取消',
        'Cancelled',
    ),
    "c044": (
        '对端未确认',
        "The peer didn't confirm",
    ),
    "c045": (
        '对端没有这个文件：%s',
        "The peer doesn't have this file: %s",
    ),
    "c046": (
        '对端拒绝发送',
        'The peer refused to send',
    ),
    "c047": (
        '字节数不符：期望 %d，收到 %d',
        'Byte count mismatch: expected %d, got %d',
    ),
    "c048": (
        '发往 %s 失败：%s',
        'Failed to send to %s: %s',
    ),
    "c049": (
        '扫描 %d 块网卡，广播 %d 次，收到 %d 个应答',
        'Scanned %d adapters, sent %d broadcasts, got %d replies',
    ),
    # ---- v1.4 完整性校验 / 续传 / 文字互传
    "c060": (
        '第 %d 段校验不通过（每段 %d MB），这次传输已作废，请重发',
        'Checksum mismatch on segment %d (%d MB each); this transfer was '
        'discarded, please send again',
    ),
    "c061": (
        '文字太长，上限 %d KB',
        'Text too long, limit is %d KB',
    ),
    "c062": (
        '收到来自对端的文字，%d 个字符',
        'Received %d characters of text from the peer',
    ),
    "c063": (
        '清理了 %d 个过期分片',
        'Cleaned up %d stale partial files',
    ),
    "c064": (
        '没有可发送的文字',
        'Nothing to send',
    ),
    "c065": (
        '对端没有接收这段文字',
        'The peer did not accept the text',
    ),
    "c066": (
        '整体校验不通过：写入的文件和源文件内容不一致，已删除这次接收的文件',
        'Full-file checksum mismatch: the written file does not match the '
        'source, the received file was deleted',
    ),
    "c067": (
        '正在校验已有分片（续传）',
        'Verifying existing partial data (resuming)',
    ),
    "c068": (
        '已续传 %s，前面 %s 是上次传的',
        'Resumed at %s, the first %s came from the previous attempt',
    ),
    # ---- v1.5.1 连不上时说什么
    "c069": (
        '连不上 %s:%s —— 这个地址上没有程序在听。对端多半没开 LanSplice，'
        '或者填的不是它现在的地址',
        'Cannot reach %s:%s — nothing is listening there. The other machine most '
        'likely has LanSplice closed, or this is not its current address',
    ),
    "c070": (
        '%s:%s 一声不响 —— 两台可能不在同一个路由器下，或者对端被防火墙挡住了。'
        '确认两台连的是同一个 WiFi / 路由器，再试一次',
        '%s:%s gave no answer — the two machines may not be on the same router, or '
        'the peer is blocked by its firewall. Check that both use the same Wi-Fi or '
        'router, then try again',
    ),
    "c071": (
        '连不上 %s:%s —— %s',
        'Cannot reach %s:%s — %s',
    ),
    "c085": (
        '收到聊天消息（%d 字）',
        'Chat message received (%d chars)',
    ),
    # ---- v1.4 托盘 / 常驻
    "g300": (
        '显示主窗口',
        'Show window',
    ),
    "g301": (
        '打开接收目录',
        'Open receive folder',
    ),
    "g302": (
        '退出 LanSplice',
        'Quit LanSplice',
    ),
    "g303": (
        '停止接收',
        'Stop receiving',
    ),
    "g304": (
        '开始接收',
        'Start receiving',
    ),
    "g305": (
        '开机自动启动',
        'Start with Windows',
    ),
    "g306": (
        '写不进开机启动项。多半是被安全软件拦了，\n'
        '可以手动把 exe 的快捷方式放进「启动」文件夹。',
        'Could not write the startup entry. Security software may have '
        'blocked it; you can put a shortcut to the exe in the Startup folder.',
    ),
    "g307": (
        '已设为开机自动启动',
        'Will start with Windows',
    ),
    "g308": (
        '已取消开机自动启动',
        'Removed from Windows startup',
    ),
    "g309": (
        '正在接收',
        'receiving',
    ),
    "g310": (
        '已停止',
        'stopped',
    ),
    "g311": (
        'LanSplice 还在后台',
        'LanSplice is still running',
    ),
    "g312": (
        '窗口已缩到托盘，接收不会中断。要真正退出请用托盘右键菜单。',
        'Minimised to the tray; receiving continues. Use the tray menu to quit.',
    ),
    # ---- v1.4 文字互传
    "g320": (
        '发文字…',
        'Send text…',
    ),
    "g321": (
        '发送到对端',
        'Send to peer',
    ),
    "g322": (
        '文字已送达 %s',
        'Text delivered to %s',
    ),
    "g323": (
        '发送文字失败：%s',
        'Could not send the text: %s',
    ),
    "g324": (
        '收到来自 %s 的文字',
        'Text from %s',
    ),
    "g325": (
        '复制到剪贴板',
        'Copy to clipboard',
    ),
    "g326": (
        '已复制',
        'Copied',
    ),
    "g327": (
        '关闭',
        'Close',
    ),
    "g328": (
        '发剪贴板',
        'Send clipboard',
    ),
    "g329": (
        '剪贴板里没有文字',
        'The clipboard has no text',
    ),
    "g330": (
        '收到文字后自动写进剪贴板',
        'Copy incoming text to the clipboard automatically',
    ),
    "g331": (
        '传完再校验文件（慢，但更可靠）',
        'Verify the file after transfer (slower, more reliable)',
    ),
    "g332": (
        '校验已有数据 %d%%',
        'Verifying existing data %d%%',
    ),
    "g333": (
        '上次连的是 %s',
        'Last connected to %s',
    ),
    "g334": (
        '正在校验 %s%%',
        'Verifying %s%%',
    ),
    "g335": (
        '续传 %s',
        'Resuming %s',
    ),
    "g336": (
        '已另存为 %s（对端有同名文件，没有覆盖）',
        'Saved as %s (a file with that name already existed, nothing was overwritten)',
    ),
    "g337": (
        '分片已保留，再点一次「发送」会自动接着传',
        'Partial data kept — press Send again to resume',
    ),
    "g340": (
        '请先在左边设备列表里选一台对端',
        'Pick a peer in the device list first',
    ),
    "g341": (
        '从剪贴板填入',
        'Fill from clipboard',
    ),
    "g342": (
        '在这里输入或粘贴要发过去的文字：',
        'Type or paste the text to send:',
    ),
    "g343": (
        '本机剪贴板',
        'Local clipboard',
    ),
    "g344": (
        '收到文字',
        'Text received',
    ),
    "g345": (
        '对端已收下（共 %d 字）',
        'Delivered (%d characters)',
    ),
    "g350": (
        '传完弹通知',
        'Notify when a transfer finishes',
    ),
    "g351": (
        '传完响一声',
        'Play a sound when a transfer finishes',
    ),
    "g352": (
        '关窗口时缩到托盘（接收不中断）',
        'Minimise to tray on close (keeps receiving)',
    ),
    "g353": (
        '开机自动启动',
        'Start with Windows',
    ),
    "g354": (
        '设置',
        'Settings',
    ),
    "g355": (
        '打开配置文件夹',
        'Open settings folder',
    ),
    # ---- v1.4 手机网页端
    "g360": (
        '手机传文件',
        'Phone transfer',
    ),
    "g361": (
        '手机和电脑连同一个路由器，用相机扫下面的码，\n'
        '浏览器打开就能收发文件 —— 手机不用装任何东西。',
        'Put the phone on the same router, scan the code with the camera,\n'
        'and use the browser to send or receive. Nothing to install.',
    ),
    "g362": (
        '口令 %s',
        'Key %s',
    ),
    "g363": (
        '复制链接',
        'Copy link',
    ),
    "g364": (
        '已复制',
        'Copied',
    ),
    "g365": (
        '打不开端口 %d，可能被别的程序占用了。\n可以换个端口再试。',
        'Could not open port %d — something else may be using it.\n'
        'Try a different port.',
    ),
    "g366": (
        '网页服务只在打开这个窗口时运行，关掉就停。',
        'The web page only runs while this window is open.',
    ),
    "g368": (
        '在浏览器打开',
        'Open in browser',
    ),
    "g369": (
        '手机扫这个码',
        'Scan this with your phone',
    ),
    # ---- v1.5 文件夹镜像
    "g370": (
        '镜像文件夹…',
        'Mirror a folder…',
    ),
    "g371": (
        '把本机一个文件夹同步到对端的接收目录：只传新增和改动过的文件，\n'
        '对端已有的文件不会被删除，只是补齐和更新。',
        'Sync a local folder into the peer\'s receive folder. Only new and '
        'changed files are sent; nothing on the peer is ever deleted.',
    ),
    "g372": (
        '源文件夹',
        'Source folder',
    ),
    "g373": (
        '对端放到',
        'On the peer, under',
    ),
    "g374": (
        '开始同步',
        'Start',
    ),
    "g375": (
        '正在扫描…',
        'Scanning…',
    ),
    "g376": (
        '第 %d / %d 个：%s',
        'File %d of %d: %s',
    ),
    "g377": (
        '同步完成：更新 %d 个，跳过 %d 个，共 %s',
        'Done: %d updated, %d skipped, %s total',
    ),
    "g378": (
        '请先选一个源文件夹',
        'Choose a source folder first',
    ),
    "g379": (
        '对端已经是最新的，没有需要同步的文件',
        'The peer is already up to date',
    ),
    "g380": (
        '（对端接收目录的根）',
        '(the receive folder root)',
    ),
    "g381": (
        '正在核对 %d / %d 个文件…',
        'Checking file %d of %d…',
    ),
    "g382": (
        '核对完 %d 个文件：要传 %d 个（%s），另外 %d 个没变',
        'Checked %d files: %d to send (%s), %d unchanged',
    ),
    # ---- v1.6 单实例 / 防火墙重放行 / 传输历史
    "g383": (
        '防火墙没放行这一版',
        'Firewall does not allow this build',
    ),
    "g384": (
        '换了新版本，防火墙要重新放行',
        'New version — the firewall rule needs updating',
    ),
    "g385": (
        '这台机器上现有的防火墙规则，没有一条能放行当前版本（v%s）。\n\n'
        '可能是还没放行过，可能规则指向旧版本，也可能被安全软件清掉了。\n\n'
        '要现在重新整理一遍吗？只会改动本软件的入站规则，并且只对内网来源开放。',
        'None of the existing firewall rules on this machine allows the current '
        'build (v%s).\n\n'
        'It may never have been allowed, the rules may point at an older version, '
        'or a security suite removed them.\n\n'
        'Recreate them now? This only touches LanSplice inbound rules and only '
        'opens them to LAN sources.',
    ),
    "g386": (
        '传输历史…',
        'Transfer history…',
    ),
    "g387": (
        '传输历史',
        'Transfer history',
    ),
    "g388": (
        '时间',
        'When',
    ),
    "g389": (
        '方向',
        'Dir',
    ),
    "g390": (
        '对端',
        'Peer',
    ),
    "g391": (
        '文件',
        'Files',
    ),
    "g392": (
        '大小',
        'Size',
    ),
    "g393": (
        '结果',
        'Result',
    ),
    "g394": (
        '发送',
        'Sent',
    ),
    "g395": (
        '接收',
        'Received',
    ),
    "g396": (
        '成功 %d，失败 %d',
        '%d ok, %d failed',
    ),
    "g397": (
        '成功 %d',
        '%d ok',
    ),
    "g398": (
        '还没有记录',
        'No records yet',
    ),
    "g399": (
        '只有「发送」记录能重发',
        'Only sent records can be resent',
    ),
    "g400": (
        '原来的文件已经不在了（可能被移动或删除）',
        'The original files are gone (moved or deleted)',
    ),
    "g401": (
        '已重新加入队列：%d 个',
        'Back in the queue: %d item(s)',
    ),
    "g402": (
        '清空全部传输历史？这一步不能撤销。',
        'Clear the whole transfer history? This cannot be undone.',
    ),
    "g403": (
        '重发选中',
        'Resend',
    ),
    "g404": (
        '打开目录',
        'Open folder',
    ),
    "g405": (
        '清空历史',
        'Clear',
    ),
    "g406": (
        '关闭',
        'Close',
    ),
    # ---- v1.6.1 历史「传了什么」
    "g407": (
        '%s 等 %d 个文件',
        '%s and %d more',
    ),
    "g408": (
        '详情',
        'Details',
    ),
    "g409": (
        '传输详情',
        'Transfer details',
    ),
    "g410": (
        '内容',
        'Name',
    ),
    "g411": (
        '文件清单（%d 个）',
        'Files (%d)',
    ),
    "g412": (
        '失败 %d 个',
        '%d failed',
    ),
    "g413": (
        '双击一行看详情',
        'Double-click a row for details',
    ),
    "g414": (
        '来源',
        'Source',
    ),
    "g415": (
        '接收目录',
        'Saved to',
    ),
    "g416": (
        '还有 %d 个没列出（只记前 %d 个）',
        '%d more not listed (first %d kept)',
    ),
    # ---- v1.6.1 镜像收藏 / 右键发送
    "g417": (
        '常用任务',
        'Saved jobs',
    ),
    "g418": (
        '源文件夹不在了，需要重新选一个',
        'Source folder is gone — pick another one',
    ),
    "g419": (
        '收藏',
        'Save',
    ),
    "g420": (
        '删除',
        'Remove',
    ),
    "g421": (
        '已收藏：%s',
        'Saved: %s',
    ),
    "g422": (
        '用 LanSplice 发送',
        'Send with LanSplice',
    ),
    "g423": (
        '资源管理器右键发送',
        'Explorer right-click send',
    ),
    "g424": (
        '已加入右键菜单，重新打开资源管理器可见',
        'Added to the right-click menu — reopen Explorer to see it',
    ),
    "g425": (
        '已从右键菜单移除',
        'Removed from the right-click menu',
    ),
    "g426": (
        '写入注册表失败，可能被安全软件拦了',
        'Could not write the registry — likely blocked by security software',
    ),
    "g427": (
        '右键传来的 %d 项已加入队列',
        '%d item(s) from Explorer added to the queue',
    ),
    "g428": (
        '许可与署名…',
        'License & credit…',
    ),
    "g429": (
        'LanSplice  ·  MIT 许可\n'
        '\n'
        '你可以：\n'
        '· 随便用 —— 家里、公司、几台机器都行，不收费\n'
        '· 随便改 —— 改成自己需要的样子，不要求你公开改动\n'
        '· 随便传 —— 原样或改过的都可以给别人\n'
        '· 并进自己的项目 —— 商用也行，MIT 不限制用途\n'
        '\n'
        '唯一的要求（两条，都很轻）：\n'
        '1. 保留版权声明 —— 分发时带上 LICENSE 里的版权行和许可声明\n'
        '2. 保留署名 —— 改过的版本，请在「关于」或说明里注明来源，例如：\n'
        '     基于 LanSplice 修改 · 原作者 永远的兰兰\n'
        '     github.com/podcatcher962/LanSplice\n'
        '\n'
        '另外：你改坏了、加的功能出问题，请不要说成是原作者的问题。\n'
        '\n'
        '第三方组件（Python、tkinter、cryptography、PyInstaller）\n'
        '各自遵循自己的许可，与本项目的 MIT 许可互不影响。\n'
        '\n'
        '完整许可文本见程序目录下的 LICENSE，或上面那个仓库地址。',
        'LanSplice  ·  MIT License\n'
        '\n'
        'You may:\n'
        '· Use it freely — home, office, as many machines as you like, no charge\n'
        '· Modify it — no obligation to publish your changes\n'
        '· Redistribute it — original or modified\n'
        '· Include it in your own project — commercial use is fine\n'
        '\n'
        'The only requirements (two, both light):\n'
        '1. Keep the copyright notice — ship the copyright line and permission\n'
        '   notice from LICENSE\n'
        '2. Keep the credit — a modified build should say where it came from,\n'
        '   in About or the docs, e.g.:\n'
        '     Based on LanSplice by Lanlan Eternal\n'
        '     github.com/podcatcher962/LanSplice\n'
        '\n'
        'Also: if your build breaks, please do not present it as the original\n'
        "author's problem.\n"
        '\n'
        'Third-party components (Python, tkinter, cryptography, PyInstaller) keep\n'
        "their own licences, independent of this project's MIT terms.\n"
        '\n'
        'Full licence text: the LICENSE file next to the program, or the repo above.',
    ),
    "g430": (
        '许可与署名',
        'License & credit',
    ),
    "g431": (
        '重发',
        'Resend',
    ),
    # ---- v1.7.1 Linux 图形界面
    "g432": (
        '防火墙（%s）需手动放行',
        'Firewall (%s): allow manually',
    ),
    "g433": (
        '手动放行',
        'Allow manually',
    ),
    "g434": (
        '复制命令',
        'Copy command',
    ),
    "g435": (
        '已复制',
        'Copied',
    ),
    "g436": (
        '为什么不能一键：\n'
        '\n'
        '改防火墙要 root 权限，而各家信创系统用的工具不一样 ——\n'
        '统信和麒麟桌面版多用 UFW，服务器版常见 firewalld，\n'
        '还有些机器只剩裸 iptables。弹授权窗口这条路在各家桌面上\n'
        '表现并不一致，失败了还会留个空转的对话框。\n'
        '\n'
        '下面这条已经按本机情况选好了，粘到终端里执行一次即可，\n'
        '规则是持久的，重启不丢。',
        'Why this is not a single click:\n'
        '\n'
        'Changing firewall rules requires root, and the tool differs\n'
        'between distributions — UFW on desktop UOS/Kylin, firewalld on\n'
        'server builds, plain iptables on minimal installs. Prompting for\n'
        'elevation behaves inconsistently across desktops, and when it\n'
        'fails you are left with a dialog that did nothing.\n'
        '\n'
        'The command below is already picked for this machine. Run it once\n'
        'in a terminal; the rule persists across reboots.',
    ),
    "g437": (
        '重新检测',
        'Check again',
    ),
    "g438": (
        '本机没有装 ufw / firewalld / iptables，可能不需要放行。'
        '如果对端连不上，先看是不是 SELinux 或安全中心拦的。',
        'No ufw / firewalld / iptables found — probably nothing to allow. '
        'If the peer still cannot connect, check SELinux or the vendor '
        'security centre.',
    ),
    "g439": (
        '这台机器没有系统托盘',
        'No system tray on this system',
    ),
    "g440": (
        '防火墙',
        'Firewall',
    ),
    # ---- v1.7.3 关闭方式选择
    "g450": (
        '关闭 LanSplice',
        'Close LanSplice',
    ),
    "g451": (
        '要让 LanSplice 继续在后台待着吗？\n\n'
        '· 最小化到托盘：窗口收起来，别人还能继续给你发文件，'
        '托盘里点一下就能叫回来\n'
        '· 彻底退出：程序完全关闭，接收端也停掉，别人就找不到你了',
        'Keep LanSplice running in the background?\n\n'
        '· Minimise to tray: the window hides, others can still send you files, '
        'click the tray icon to bring it back\n'
        '· Quit completely: the program and the receiver stop, '
        'and others can no longer reach you',
    ),
    "g452": (
        '最小化到托盘',
        'Minimise to tray',
    ),
    "g453": (
        '彻底退出',
        'Quit completely',
    ),
    "g454": (
        '记住我的选择，以后不再问',
        "Remember my choice, don't ask again",
    ),
    "g455": (
        '已缩到托盘，接收继续。',
        'Minimised to tray; still receiving.',
    ),
    "g456": (
        '设置 → 关闭窗口时，可以改回来。',
        'You can change this later in Settings → When closing the window.',
    ),
    "g457": (
        '关闭窗口时',
        'When closing the window',
    ),
    "g460": (
        "内网聊天",
        "LAN chat",
    ),
    "g461": (
        "发送",
        "Send",
    ),
    "g462": (
        "在线 %d 人",
        "%d online",
    ),
    "g463": (
        "还没人在线。同一局域网里打开 LanSplice、配对码一致的人会出现在这里。",
        "Nobody online yet. Anyone on this LAN running LanSplice with the same pairing code shows up here.",
    ),
    "g464": (
        "说点什么…（回车发送，Shift+回车换行）",
        "Say something… (Enter to send, Shift+Enter for a new line)",
    ),
    "g465": (
        "我",
        "Me",
    ),
    "g466": (
        "%s 发来消息",
        "Message from %s",
    ),
    "g467": (
        "发送失败：%s",
        "Failed: %s",
    ),
    "g468": (
        "已发给 %d 人",
        "Sent to %d",
    ),
    "g469": (
        "发送中…",
        "Sending…",
    ),
    "g470": (
        "我的显示名",
        "My display name",
    ),
    "g471": (
        "名字改了，别人看到的也是这个。",
        "This is what others see.",
    ),
    "g472": (
        "清空聊天记录",
        "Clear chat history",
    ),
    "g473": (
        "确定清空本机聊天记录吗？这个操作只影响你自己这台。",
        "Clear the chat history on this machine? Only affects this computer.",
    ),
    "g474": (
        "个设备在线",
        "devices online",
    ),
    "g475": (
        "今天",
        "Today",
    ),
    "g476": (
        "没有人可以发——先确认对方也在同一局域网、配对码一致。",
        "Nobody to send to — make sure the others are on this LAN with the same code.",
    ),
    "g477": (
        '这次的防火墙规则没能生效。\n\n'
        '请再点一次「一键放行」。如果还是这样，多半是这两种情况：\n'
        '· 公司或学校的域策略规定了规则，本机改不动\n'
        '· 装了第三方安全软件，它接管了防火墙\n\n'
        '这两种都要管理员放行 TCP %d、UDP %d 与 TCP %d（只对内网）。\n'
        '把这一屏截图发给他，比转述快。',
        "The firewall rules didn't take effect this time.\n\n"
        "Click 'Allow in firewall' again. If it still fails, it's usually one of two things:\n"
        "· a domain policy from work or school fixes the rules, so this machine can't change them\n"
        "· a third-party security suite has taken over the firewall\n\n"
        "Either way an administrator has to allow TCP %d, UDP %d and TCP %d (private networks only).\n"
        "A screenshot of this message is the quickest thing to send them.",
    ),
    "g478": (
        '防火墙规则没生效，点「一键放行」重试',
        'Firewall rules not in effect — click Allow to retry',
    ),
    "g479": (
        "还没授权，防火墙没改。想放行随时点「一键放行」。",
        "Not authorised — the firewall is unchanged. Click Allow in firewall when ready.",
    ),
    # ---- v1.8 目录自动同步
    "g480": (
        "自动同步…",
        "Auto-sync…",
    ),
    "g481": (
        "盯住本机一个文件夹，有变化就推给对端。只做加法：本地删掉的文件，"
        "对端那份不会被删；同一个文件改过会覆盖对端的旧版本。关掉窗口不影响同步。",
        "Watches a local folder and pushes changes to the peer. Add-only: files you "
        "delete locally stay on the peer. An edited file replaces the peer's old copy. "
        "Closing this window does not stop syncing.",
    ),
    "g482": (
        "本地文件夹",
        "Local folder",
    ),
    "g483": (
        "对端目录",
        "On the peer",
    ),
    "g484": (
        "状态",
        "Status",
    ),
    "g485": (
        "添加…",
        "Add…",
    ),
    "g486": (
        "移除",
        "Remove",
    ),
    "g487": (
        "立即同步一次",
        "Sync now",
    ),
    "g488": (
        "选择要同步的本地文件夹",
        "Choose the local folder to sync",
    ),
    "g489": (
        "对端目录名",
        "Folder name on the peer",
    ),
    "g490": (
        "空闲",
        "Idle",
    ),
    "g491": (
        "同步中",
        "Syncing",
    ),
    "g492": (
        "失败",
        "Failed",
    ),
    "g493": (
        "已同步 %d 个（%s）",
        "Synced %d (%s)",
    ),
    "g494": (
        "上次同步：%s",
        "Last sync: %s",
    ),
    "g495": (
        "还没有同步任务。点「添加…」选一个文件夹。",
        "No sync jobs yet. Click Add… and pick a folder.",
    ),
    "g496": (
        "这个文件夹已经在列表里了。",
        "That folder is already in the list.",
    ),
    "g497": (
        "自动同步当前是关着的，先在下面勾上「开着程序就同步」。",
        "Auto-sync is off. Tick “Sync while running” below first.",
    ),
    "g498": (
        "还没选对端。先在左边列表里选一台设备。",
        "No peer selected. Pick a device on the left first.",
    ),
    "g499": (
        "自动同步已暂停，勾上开关继续。",
        "Auto-sync paused. Tick the switch to resume.",
    ),
    "g500": (
        "文件太多（超过 %d 个），这个任务暂停了。",
        "Too many files (over %d) — this job is paused.",
    ),
    "g501": (
        "这个版本没有带自动同步模块。",
        "This build does not include the auto-sync module.",
    ),
    "g502": (
        "开着程序就同步",
        "Sync while running",
    ),
    "g503": (
        "对端接收目录下的子目录名，留空就用文件夹名。",
        "Subfolder under the peer's receive folder. Empty = same name as the local folder.",
    ),
    "g505": (
        "自动同步：推送了 %d 个文件（%s）",
        "Auto-sync: pushed %d file(s) (%s)",
    ),
    "g506": (
        "自动同步出错：%s",
        "Auto-sync error: %s",
    ),
    "g507": (
        "等待变化。改动的文件会在十几秒内推到对端。",
        "Waiting for changes. Edits are pushed within a few seconds.",
    ),
    "g508": (
        "手机接入已开启（端口 %d），安卓客户端和网页都能随时连。",
        "Phone access is on (port %d) — the Android app and the web page can connect any time.",
    ),
    "g509": (
        "手机接入没开起来（端口 %d）：%s。二维码照常可用，只是手机连不上。",
        "Phone access could not start (port %d): %s. The QR code still works, but phones cannot connect.",
    ),
    # ---- v1.9 电脑 → 手机
    "g510": (
        "手机接入没开起来，文件没地方放。先在「文件 → 手机传文件」里把它打开。",
        "Phone access is not running, so there is nowhere to put the file. "
        "Open File → Send to phone first.",
    ),
    "g511": (
        "选择要发到手机的文件（可多选）",
        "Choose files to send to the phone (multiple allowed)",
    ),
    "g511a": (
        "发文件到手机…",
        "Send files to phone…",
    ),
    "g512": (
        "选择要发到手机的文件夹（会打包成一个 zip）",
        "Choose a folder to send (it will be zipped)",
    ),
    "g512a": (
        "发文件夹到手机…",
        "Send folder to phone…",
    ),
    "g513": (
        "已放好 %d 个文件（%s）。\n\n"
        "手机上打开 LanSplice，页面最上方「电脑发来的文件」里点「下载」即可。\n"
        "没看到就下拉刷新一下 —— 页面每 5 秒自己也会刷。",
        "%d file(s) staged (%s).\n\n"
        "Open LanSplice on the phone and tap Download under "
        "\"Files from your PC\" at the top of the page.\n"
        "If it is not there yet, pull to refresh — the page also polls every 5 seconds.",
    ),
    "g516": (
        "有几个没放进去：\n%s",
        "Some files could not be staged:\n%s",
    ),
    "g517": (
        "已放到手机收件：%d 个（%s），手机上点下载即可",
        "Staged for the phone: %d file(s) (%s) — tap Download on the phone",
    ),
    # ---- v1.9 深色主题
    "g520": (
        "浅色主题",
        "Light theme",
    ),
    "g521": (
        "深色主题",
        "Dark theme",
    ),
    "g522": (
        "跟随系统",
        "Follow system",
    ),
    # ---- v1.9.2 设备列表里的「手机」入口
    "g530": (
        '手机 · 扫码或用 App 连接',
        'Phone · scan QR or use the app',
    ),
    "g531": (
        '手机不广播、也不开接收端口，所以「查找设备」里没有它；扫码就能连上',
        'Phones do not broadcast and open no port, so "Find devices" never lists one — '
        'scan the QR code instead',
    ),
    # ---- v1.5 命令行
    "cli01": (
        '没有找到配对码。两种办法：打开一次图形界面让它生成，'
        '或者直接加 --code XXXX-XXXX-XXXX-XXXX（要和对面那台上显示的一致）。',
        'No pairing code found. Either run the GUI once so it can generate one, '
        'or pass --code XXXX-XXXX-XXXX-XXXX (it must match what the other machine shows).',
    ),
    "cli02": (
        '地址格式不对：%s（应形如 192.168.1.20 或 192.168.1.20:47820）',
        'Bad address: %s (expected 192.168.1.20 or 192.168.1.20:47820)',
    ),
    "cli03": (
        '没有找到可发送的文件',
        'Nothing to send',
    ),
    "cli04": (
        '准备发送 %d 个文件，共 %s → %s:%d',
        'Sending %d file(s), %s total → %s:%d',
    ),
    "cli05": (
        '配对码不对，对端拒绝了这次连接',
        'Wrong pairing code — the peer refused the connection',
    ),
    "cli06": (
        '连不上对端：%s',
        'Cannot reach the peer: %s',
    ),
    "cli07": (
        '  已跳过（对端已有同大小同时间的文件）',
        '  skipped (same size and mtime already on the peer)',
    ),
    "cli08": (
        '  对端有同名文件，存成了 %s',
        '  saved as %s (name already taken on the peer)',
    ),
    "cli09": (
        '  失败：%s',
        '  failed: %s',
    ),
    "cli10": (
        '完成：成功 %d，跳过 %d，失败 %d，用时 %.1f 秒，平均 %.1f MB/s',
        'Done: %d sent, %d skipped, %d failed, %.1f s, %.1f MB/s average',
    ),
    "cli11": (
        '正在扫描局域网（约 2 秒）…',
        'Scanning the LAN (~2 s)…',
    ),
    "cli12": (
        '没找到设备。检查两台是否在同一个路由器下、对端是否开着接收。',
        'No devices found. Check that both are on the same router and the '
        'peer is receiving.',
    ),
    "cli13": (
        '共找到 %d 台',
        '%d device(s) found',
    ),
    # ---- v1.7 接收端（serve）
    "cli14": (
        'LanSplice %s · 接收端',
        'LanSplice %s · receiver',
    ),
    "cli15": (
        '本机原来没有配对码，已生成并保存：%s（对端填这个）',
        'No pairing code existed here; generated and saved: %s (use this on the peer)',
    ),
    "cli16": (
        '接收目录不可用：%s',
        'Receive folder is not usable: %s',
    ),
    "cli17": (
        '端口 %d 起不来：%s（可能被别的程序占用，换 --port 试试）',
        'Cannot listen on port %d: %s (maybe taken; try another --port)',
    ),
    "cli18": (
        '监听 %s:%d',
        'listening on %s:%d',
    ),
    "cli19": (
        '  接收 %s（%s）',
        '  receiving %s (%s)',
    ),
    "cli20": (
        '  从断点 %s 继续',
        '  resumed from %s',
    ),
    "cli21": (
        '  已保存 %s（%s）',
        '  saved %s (%s)',
    ),
    "cli22": (
        '  失败 %s：%s',
        '  failed %s: %s',
    ),
    "cli23": (
        '  收到文字：%s',
        '  text received: %s',
    ),
    "cli24": (
        '接收目录 %s',
        'receive folder %s',
    ),
    "cli25": (
        '配对码 %s（对端 send 时用 --code 传这个）',
        'pairing code %s (pass it as --code on the sender)',
    ),
    "cli26": (
        '等待连接…按 Ctrl+C 结束',
        'waiting for connections… press Ctrl+C to stop',
    ),
    "cli27": (
        '共收到 %d 个文件，%s，失败 %d，时长 %.1f 秒',
        'received %d file(s), %s, %d failed, %.1f s',
    ),
    "cli28": (
        '没有参数。可用子命令：serve（当接收端）、send（发送）、'
        'devices（找设备）、version（版本）。加 -h 看详细用法。',
        'No arguments. Subcommands: serve (receive), send, devices, version. '
        'Use -h for details.',
    ),

    # ---- 网络体检（v2.0.0 并入主程序）
    "g532": ('网络体检', 'Network checkup'),
    "g533": ('本机与网关', 'This PC & gateway'),
    "g534": ('局域网设备', 'LAN devices'),
    "g535": ('体检结论', 'Findings'),
    "g536": ('对端 IP（可选）', 'Peer IP (optional)'),
    "g537": ('开始体检', 'Run checkup'),
    "g538": ('体检中…', 'Checking…'),
    "g539": ('重新体检', 'Run again'),
    "g541": ('导出报告', 'Export report'),
    "g542": ('关闭', 'Close'),
    "g543": ('准备就绪', 'Ready'),
    "g544": ('网关', 'Gateway'),
    "g545": ('外网', 'Internet'),
    "g546": ('局域网', 'LAN'),
    "g547": ('地址', 'Address'),
    "g548": ('类型', 'Type'),
    "g549": ('名称 / 型号', 'Name / model'),
    "g550": ('路由器', 'Router'),
    "g551": ('电脑', 'PC'),
    "g552": ('手机', 'Phone'),
    "g553": ('其他', 'Other'),
    "g554": ('正在体检…', 'Checking…'),
    "g555": ('完成，用时 %.1f 秒', 'Done in %.1f s'),
    "g556": ('体检失败', 'Checkup failed'),
    "g557": ('还没有结果', 'No result yet'),
    "g558": ('先点「开始体检」，再导出报告。', 'Run a checkup before exporting.'),
    "g559": ('保存体检报告', 'Save checkup report'),
    "g560": ('报告已保存：%s', 'Report saved: %s'),
    "g561": ('报告已保存', 'Report saved'),
    "g562": ('要现在打开看看吗？\n\n%s', 'Open it now?\n\n%s'),
    "g563": ('共 %d 台　·　邻居表 + SSDP + LanSplice 广播',
             '%d device(s)　·　ARP + SSDP + LanSplice broadcast'),
    "g564": ('运行中', 'Running'),
    "g565": ('未运行', 'Not running'),
    "g566": ('端口被占', 'Port in use'),
    "g567": ('网关 %s　外网探测 %s', 'Gateway %s　probe %s'),
    "g568": ('%s　MAC %s　·　来源 %s', '%s　MAC %s　·　from %s'),
    "g569": ('没有 MAC 记录', 'no MAC record'),
    "g570": ('对端 IP 形如 192.168.0.20。', 'Peer IP looks like 192.168.0.20.'),
    "g571": ('IP 格式不对', 'Bad IP address'),
    "g572": ('体检', 'Checkup'),
    "g573": ('没有联网', 'not connected'),
    "g574": ('无线', 'Wi-Fi'),
    "g575": ('有线', 'Wired'),
    "g577": ('体检失败：%s', 'Checkup failed: %s'),
    "g578": ('不通', 'unreachable'),
    "g579": ('网络体检', 'Network checkup'),
    "g580": ('连不上时，先看这里', 'when a transfer fails, start here'),
    "g581": ('%d 台', '%d device(s)'),

    # ---- 体检结论（netcheck_rules.py）
    # 这些是「证据 → 结论」那段文字。窗口标题、按钮早就双语了，但结论一直
    # 写死在规则里，于是英文界面一跑体检，右侧整栏还是中文。
    "d001": ('有条规则没跑完', 'A rule did not finish'),
    "d002": ('没有发现问题', 'No problems found'),
    "d003": ('本机、链路、端口都正常。',
             'This PC, the link and the ports all look fine.'),
    "d004": ('本机没有可用的 IPv4 地址',
             'This PC has no usable IPv4 address'),
    "d005": ('没找到任何一块已联网的网卡，或者只有 169.254 开头的自动地址。',
             'No connected adapter was found, or the only address is a '
             '169.254 self-assigned one.'),
    "d006": ('先确认网线插好 / Wi-Fi 已连上，再点一次体检。',
             'Check the cable or the Wi-Fi connection, then run the checkup again.'),
    "d007": ('本机有 %d 个 IPv4 地址，其中 %d 个像虚拟网卡',
             'This PC has %d IPv4 addresses (%d virtual-looking)'),
    "d008": ('实体：%s；虚拟：%s。装了 VMware / VirtualBox / Hyper-V / VPN 的机器，'
             'UDP 广播可能被系统挑中虚拟网卡，真实局域网里的对端就收不到。',
             'Physical: %s; virtual: %s. On machines with VMware / VirtualBox / '
             'Hyper-V / VPN, the system may send UDP broadcasts out of a virtual '
             'adapter, so the peer on the real LAN never receives them.'),
    "d009": ('本机有 %d 块网卡，注意广播从哪块出去',
             'This PC has %d adapters — watch which one carries the broadcast'),
    "d010": ('检测到这些地址：%s。都是实体网卡时广播会各自发出，一般不影响；'
             '如果对端仍然收不到，先确认两台机器在同一网段。',
             'Addresses found: %s. Broadcasts go out on every physical adapter, so '
             'this is usually harmless. If the peer still cannot see you, first make '
             'sure both machines are on the same subnet.'),
    "d011": ('LanSplice 已经是按每块网卡各发一遍广播；如果仍发现不到对端，'
             '先临时禁用虚拟网卡再试。',
             'LanSplice already broadcasts on every adapter; if the peer is still '
             'not found, temporarily disable the virtual adapter and try again.'),
    "d012": ('无', 'none'),
    "d013": ('、', ', '),
    "d014": ('到网关丢包 %.0f%%，链路本身有问题',
             '%.0f%% packet loss to the gateway — the link itself is at fault'),
    "d015": ('网关 %s：发 %d 个包只回来 %d 个。',
             'Gateway %s: only %d of %d probes came back.'),
    "d016": ('先换根网线或换个交换机口；无线的话靠近路由器再测一次。',
             'Try another cable or switch port; on Wi-Fi, move closer to the '
             'router and test again.'),
    "d017": ('到网关有轻微丢包（%.0f%%）',
             'Slight packet loss to the gateway (%.0f%%)'),
    "d018": ('网关 %s：平均 %.1f ms，抖动 %.1f ms。',
             'Gateway %s: %.1f ms average, %.1f ms jitter.'),
    "d019": ('偶尔丢包通常是无线信号或网线接触问题，传大文件会明显变慢。',
             'Occasional loss is usually a weak Wi-Fi signal or a loose cable; '
             'large transfers will slow down noticeably.'),
    "d020": ('到网关抖动 %.0f ms，链路不稳',
             '%.0f ms jitter to the gateway — unstable link'),
    "d021": ('平均 %.1f ms，但相邻两次最多差 %.0f ms。',
             '%.1f ms average, but consecutive probes differ by up to %.0f ms.'),
    "d022": ('无线信号弱或信道拥挤时常见。换 5GHz、或靠近路由器。',
             'Common with a weak signal or a crowded channel. Switch to 5 GHz or '
             'move closer to the router.'),
    "d023": ('到网关延迟偏高（%.0f ms）', 'High latency to the gateway (%.0f ms)'),
    "d024": ('有线网络到自己的路由器一般应该在 1~3 ms。',
             'A wired link to your own router should normally be 1–3 ms.'),
    "d025": ('检查是不是走了电力猫、Wi-Fi 中继，或者路由器负载过高。',
             'Check for powerline adapters, Wi-Fi repeaters, or an overloaded router.'),
    "d026": ('到网关正常', 'Gateway OK'),
    "d027": ('%s：%d/%d 个包回来，平均 %.1f ms，抖动 %.1f ms。',
             '%s: %d/%d probes returned, %.1f ms average, %.1f ms jitter.'),
    "d028": ('外网探测不通（可能被路由器禁了 ICMP）',
             'Internet probe failed (the router may block ICMP)'),
    "d029": ('发 %d 个包回来 %d 个。能上网但 ping 不通是常见配置，不一定是故障。',
             '%d of %d probes returned. Blocking ping while the internet still '
             'works is a common setup, not necessarily a fault.'),
    "d030": ('改用浏览器打开任意网站验证；能开就忽略这条。',
             'Open any website in a browser to confirm; if it loads, ignore this.'),
    "d031": ('外网丢包 %.0f%%', '%.0f%% packet loss to the internet'),
    "d032": ('平均 %.1f ms，抖动 %.1f ms。', '%.1f ms average, %.1f ms jitter.'),
    "d033": ('如果局域网内传文件不受影响，问题在上游宽带，不是你的设备。',
             'If LAN transfers are unaffected, the problem is upstream with your '
             'ISP, not with your devices.'),
    "d034": ('外网正常', 'Internet OK'),
    "d035": ('平均 %.1f ms，抖动 %.1f ms，丢包 %.0f%%。',
             '%.1f ms average, %.1f ms jitter, %.0f%% loss.'),
    "d036": ('局域网里只看到自己', 'Only this PC is visible on the LAN'),
    "d037": ('邻居表是空的，连网关的 MAC 都没缓存到。',
             'The neighbor table is empty — not even the gateway MAC is cached.'),
    "d038": ('无线网络如果是「访客网络」或开了 AP 隔离，设备之间互相看不见，'
             '这种网络下任何局域网直传都用不了。',
             'On a guest network or with AP isolation enabled, devices cannot see '
             'each other, and no LAN transfer tool will work.'),
    "d039": ('局域网里只有网关一台设备', 'Only the gateway is visible on the LAN'),
    "d040": ('这可能是对的——其他设备没开机，或者处于省电休眠。'
             '也可能是路由器开了无线客户端隔离。',
             'This may be correct: other devices are off or dozing. Or the router '
             'has wireless client isolation enabled.'),
    "d041": ('让对端电脑先打开 LanSplice，再点一次体检。',
             'Start LanSplice on the peer, then run the checkup again.'),
    "d042": ('局域网里看到 %d 台设备', '%d device(s) visible on the LAN'),
    "d043": ('邻居表里有记录，说明二层是通的。',
             'The neighbor table has entries, so layer 2 is working.'),
    "d044": ('端口被别的程序占着：%s', 'Port held by another program: %s'),
    "d045": ('%s（%s）', '%s (%s)'),
    "d046": ('LanSplice 需要 47820（传输）和 47822（手机网页）。'
             '被别的程序先占了，它自己会起不来或者只能半残。',
             'LanSplice needs 47820 (transfer) and 47822 (phone page). If another '
             'program grabbed them first, LanSplice will not start or will only '
             'half work.'),
    "d047": ('关掉上面那个程序再启动 LanSplice；或在它的 config.json 里换端口。',
             'Close that program and start LanSplice again, or change the port in '
             'its config.json.'),
    "d048": ('LanSplice 正在运行', 'LanSplice is running'),
    "d049": ('47820 / 47822 已经在监听（进程 %s），端口这块不用担心。',
             '47820 / 47822 are already listening (process %s) — no port problem.'),
    "d050": ('对端填的是本机地址 %s', 'The peer address is this PC itself (%s)'),
    "d051": ('这台机器自己就是 %s，自己连自己看不出任何问题。',
             'This machine is %s itself; connecting to yourself proves nothing.'),
    "d052": ('换成另一台电脑的 IP 再体检；想看本机状态的话，左边那栏已经够了。',
             'Use another computer\'s IP and run the checkup again; the left column '
             'already covers this PC.'),
    "d053": ('对端 %s 完全没有响应', 'Peer %s does not respond at all'),
    "d054": ('ICMP 发了 %d 个包一个没回，47820 / 47822 也连不上。',
             'All %d ICMP probes went unanswered, and neither 47820 nor 47822 '
             'accepts a connection.'),
    "d055": ('三种可能：对端没开机 / 不在同一个网段 / 它的防火墙把一切都挡了。'
             '先看对端 IP 前三位是否和你一样。',
             'Three possibilities: the peer is off, it is on another subnet, or its '
             'firewall blocks everything. First check that the first three octets '
             'of its IP match yours.'),
    "d056": ('对端 %s 在线，传输端口通', 'Peer %s is up, transfer port open'),
    "d057": ('47820 可以连上，文件传输这条路没障碍。',
             '47820 accepts connections, so file transfer has a clear path.'),
    "d058": ('它不回应 ping（Windows 防火墙默认挡 ICMP 回显，很常见），'
             '但传输端口是通的，不影响使用。',
             # 这一条是接在上一句后面的，英文之间要留一个空格
             ' It does not answer ping (Windows Firewall blocks inbound ICMP by '
             'default — very common), but the transfer port is open, so nothing '
             'is affected.'),
    "d059": ('对端开着 LanSplice 手机页，但传输端口没开',
             'Peer serves the LanSplice phone page, but the transfer port is closed'),
    "d060": ('47822 通、47820 不通——可能是只开了「手机传文件」没开主服务。',
             '47822 is open but 47820 is not — maybe only "phone transfer" is '
             'running, not the main service.'),
    "d061": ('在对端点一次「一键放行防火墙」，再确认主界面在运行。',
             'Click "Allow in firewall" on the peer and make sure its main window '
             'is running.'),
    "d062": ('对端在线，但 LanSplice 的两个端口都不通',
             'Peer is up, but neither LanSplice port is open'),
    "d063": ('ping 得通说明机器活着；47820 / 47822 都不通，'
             '最常见的是对端没开软件，其次是 Windows 防火墙拦了入站。',
             'Ping works, so the machine is alive; both 47820 and 47822 are closed. '
             'Most often LanSplice is simply not running on the peer, or Windows '
             'Firewall blocks inbound traffic.'),
    "d064": ('让对端打开 LanSplice，点一次「一键放行防火墙」。',
             'Start LanSplice on the peer and click "Allow in firewall".'),
    "d065": ('能 ping 通却连不上，常见于无线客户端隔离',
             'Ping works but connections fail — often Wi-Fi client isolation'),
    "d066": ('同一路由器下，开了「AP 隔离 / 客户端隔离」时，'
             '设备之间 ping 可能通，但 TCP 连接被拦。',
             'With "AP isolation / client isolation" enabled on the same router, '
             'devices may still ping each other while TCP connections are blocked.'),
    "d067": ('如果这台是连 Wi-Fi 的：换有线试一次，或者登录路由器关掉 AP 隔离。',
             'If this PC is on Wi-Fi, try a cable, or log in to the router and '
             'disable AP isolation.'),
    "d068": ('端口通，但广播发现不到对端',
             'Port is open, but broadcast cannot find the peer'),
    "d069": ('单播能连上、广播收不到，说明组播/广播被拦了，'
             '或者你们俩不在同一个广播域。',
             'Unicast connects but broadcast does not arrive, so multicast/broadcast '
             'is blocked, or the two machines are in different broadcast domains.'),
    "d070": ('在 LanSplice 里直接填对端 IP 连接，不要依赖「重新查找设备」。',
             'Enter the peer IP directly in LanSplice instead of relying on '
             '"Find devices again".'),
    "d071": ('读取本机网卡…', 'Reading local adapters…'),
    "d072": ('探测局域网、延迟、端口…', 'Probing LAN, latency, ports…'),
    "d073": ('出结论…', 'Drawing conclusions…'),
    "d074": ('邻居表', 'ARP table'),
    "d075": ('LanSplice 在线', 'LanSplice online'),

    # ---- 体检报告（netcheck_report.py）
    "d080": ('问题', 'Problem'),
    "d081": ('注意', 'Notice'),
    "d082": ('正常', 'OK'),
    "d083": ('无数据', 'No data'),
    "d084": ('没有测得数据。', 'No measurements were collected.'),
    "d085": ('平均', 'avg'),
    "d086": ('最小 / 最大', 'min / max'),
    "d087": ('抖动', 'jitter'),
    "d088": ('丢包', 'loss'),
    "d089": ('样本：%s', 'Samples: %s'),
    "d090": ('对端 %s', 'Peer %s'),
    "d091": ('端口', 'Ports'),
    "d092": ('%s（%s）', '%s (%s)'),
    "d093": ('没有开放端口', 'no open ports'),
    "d094": ('LanSplice 网络体检报告 %s', 'LanSplice Network Checkup Report %s'),
    "d095": ('LanSplice 网络体检报告', 'LanSplice Network Checkup Report'),
    "d096": ('%s　·　耗时约 %s 秒', '%s　·　about %s s'),
    "d097": ('问题 %d · 注意 %d · 正常 %d',
             'Problem %d · Notice %d · OK %d'),
    "d099": ('掩码', 'Mask'),
    "d100": ('广播地址', 'Broadcast'),
    "d101": ('链路', 'Link'),
    "d102": ('网卡', 'Adapter'),
    "d103": ('速率', 'Speed'),
    "d105": ('网关与外网', 'Gateway & internet'),
    "d106": ('网关 %s', 'Gateway %s'),
    "d107": ('外网 %s', 'Internet %s'),
    "d109": ('名称', 'Name'),
    "d110": ('来源', 'Source'),
    "d113": ('LanSplice v%s · 网络体检　·　由 © 永远的兰兰 制作　·　'
             '报告不含任何加密密钥，可放心转发',
             'LanSplice v%s · Network checkup　·　by © Lanlan Eternal　·　'
             'this report contains no keys and is safe to forward'),
    # 常见端口的中文名（报告里 47820（LanSplice 传输）那种写法）
    "d120": ('SMB 共享', 'SMB share'),
    "d121": ('NAS / 路由器', 'NAS / router'),
    "d122": ('HTTP 代理', 'HTTP proxy'),
    "d123": ('打印机', 'printer'),
    "d124": ('LanSplice 传输', 'LanSplice transfer'),
    "d125": ('LanSplice 手机页', 'LanSplice phone page'),

    # ---- v2.1.0 群发 / 多机
    "g582": ('正在发往第 %d/%d 台：%s', 'Sending to %d/%d: %s'),
    "g584": ('群发完成：%d 台成功，%d 台失败 · 共 %s',
             'Group send: %d ok, %d failed · %s'),
    "g585": ('✔ %s  %s', '✔ %s  %s'),
    "g586": ('✘ %s  %s', '✘ %s  %s'),
    "g587": ('%d 个文件', '%d file(s)'),
    "g588": ('，跳过 %d 个', ', %d skipped'),
    "g589": ('，失败 %d 个', ', %d failed'),
    "g590": ('群发结果', 'Group send result'),
    "g591": ('①  群发 %d 台', '①  Send to %d'),
    "g592": ('已选 %d 台 — 会依次发给每一台',
             '%d selected — sends to each in turn'),
    "g593": ('Ctrl 点选可多台', 'Ctrl-click for more'),
}

LANGS = ("zh", "en")
_lang = "zh"


def set_lang(lang):
    global _lang
    _lang = lang if lang in LANGS else "zh"
    return _lang


def get_lang():
    return _lang


def is_en():
    return _lang == "en"


def t(key):
    row = S.get(key)
    if not row:
        return key
    return row[1] if _lang == "en" else row[0]
