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
        '连接诊断…',
        'Connection diagnosis…',
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
        '（没找到，点「手动填写对端地址」）',
        "(not found — click 'Enter peer address')",
    ),
    "g080": (
        '没找到设备 · 本机有 %d 个地址，见「工具 → 本机网络详情」',
        'No devices found · this PC has %d addresses, see Tools → My network details',
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
        '主机名：%s\n\n本机地址：\n%s\n\n两台机器要互传，必须各有一条**同网段**的地址。\n192.168.56.x / 192.168.51.x / 172.17.x 这类基本是\n虚拟机、Hyper-V 或 VPN 的虚拟网卡，只有本机内部存在，\n对端连不上，发现广播也到不了那里。\n\n如果在列表里看到 192.168.0.x（或你家路由器那个网段），\n就用那条地址。',
        "Host name: %s\n\nAddresses on this PC:\n%s\n\nBoth machines need an address on the **same subnet**.\n192.168.56.x / 192.168.51.x / 172.17.x are usually virtual\nadapters from a VM, Hyper-V or a VPN — they only exist inside\nthis machine, so the peer can neither reach them nor hear the\ndiscovery broadcast there.\n\nIf you see a 192.168.0.x address (or whatever your router uses),\nthat's the one to use.",
    ),
    "g094": (
        '本机网络详情',
        'My network details',
    ),
    "g095": (
        '还没选对端。先点「工具 → 重新查找设备」。',
        'No peer selected. Use Tools → Find devices again.',
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
        '还没选对端。点「工具 → 重新查找设备」。',
        'No peer selected. Use Tools → Find devices again.',
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
        '输入对端接收目录下的相对路径（例如  城市声音志\\北京）：',
        "Enter a path relative to the peer's receive folder (e.g. Albums\\Beijing):",
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
        '端口一直被占用。多半是**另一个窗口还开着**（旧版本、或者点了两次图标）。\n把多余的窗口关掉，再点「工具 → 接收端开关」重开。',
        'The port stays busy. Usually **another copy of the app is still running** (an older version, or you double-clicked the icon).\nClose the extra window, then use Tools → Receiver on/off to start it again.',
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
        '本机配对码：\n\n        %s\n\n把这串码抄到另一台，在「安全 → 填写对端配对码」里填进去。\n\n或者反过来，把另一台的码填到本机。两台一致才能连上。\n\n配对码属于密码，别发到群里、别截图外传。',
        "Pairing code for this PC:\n\n        %s\n\nCopy this code to the other machine and enter it under Security → Enter peer pairing code.\n\nOr the other way round: enter the other machine's code here. Both must match before they can connect.\n\nTreat it like a password — don't post it in group chats or share screenshots.",
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
        "Windows has classified one of your network adapters as a **Public network**.\n\nThis app used to allow traffic only on Private networks, so on a Public\nnetwork the port stays closed — which is the most common reason two machines\non the same subnet still can't see each other.\n\nSuggestion: switch the home network to Private. This does NOT expose this PC\nto the internet — it only tells Windows 'this is my trusted home network'.\n\nSwitch it to Private and rebuild the firewall rules?\n(Choose No to only relax the firewall and leave the network category alone)",
    ),
    "g176": (
        '放行防火墙',
        'Allow in firewall',
    ),
    "g177": (
        '会重新整理本软件的防火墙规则：\n\n  1. 删掉 Windows 自动建的宽松规则\n  2. 重建两条严格规则：TCP %d、UDP %d\n  3. 只允许 192.168.0.0/16、10.0.0.0/8、172.16.0.0/12 这些内网段，\n     公网来源无论如何都进不来\n  4. 规则只认本程序这个 exe，本机别的软件借不到这两个端口\n\n%s\n\n需要点一次「是」授权（管理员权限）。继续？',
        "This will rebuild the firewall rules for this app:\n\n  1. Delete the loose rule Windows created automatically\n  2. Create two strict rules: TCP %d, UDP %d\n  3. Allow only 192.168.0.0/16, 10.0.0.0/8 and 172.16.0.0/12 (private ranges),\n     so internet sources can never get in\n  4. The rules match this exe only — other programs on this PC cannot borrow the ports\n\n%s\n\nYou'll get one administrator prompt. Continue?",
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
        '已重设。当前规则 %d 条%s。\n\n%s\n\n如果刚才在 UAC 点了「否」，规则不会变，可以再点一次。\n\n验证：另一台点「工具 → 重新查找设备」。',
        'Done. %d rule(s) now%s.\n\n%s\n\nIf you clicked No on the UAC prompt, nothing changed — just run it again.\n\nVerify: on the other machine, click Tools → Find devices again.',
    ),
    "g183": (
        '（启用中）',
        ' (enabled)',
    ),
    "g184": (
        '（未生效，检查是否授权成功）',
        ' (not active — check that you approved the UAC prompt)',
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
        '① 两台机器各开一次，左边会显示本机配对码。\n② 让两台的配对码一致：\n   点「复制配对码」，到另一台点「填写对端配对码」粘贴。\n③ 工具 → 重新查找设备，选中对端。\n④ 把文件或文件夹拖进虚线框（也可以点「选择文件/文件夹」）。\n⑤ 点「① 发送到对端」。\n\n文件会存到对端的接收目录（默认 E:\\_xfer），目录结构保持不变。\n同名同大小的文件会自动跳过，不会重传。\n\n首次使用如果对端找不到本机，到「安全 → 放行防火墙」点一次。\n\n'
        '—— 1.4 新增 ——\n'
        '· 断点续传：传一半断了，再点一次「发送」会从断的地方接着传，不用从头来。\n'
        '· 同名不覆盖：对端已经有同名文件时，自动存成「xxx (2).ext」，绝不顶掉旧的。\n'
        '· 发文字：Ctrl+Shift+V 把本机剪贴板直接推到对端，对端点一下就能粘贴。\n'
        '· 手机传文件：文件 → 手机传文件，手机扫二维码用浏览器收发，手机不用装任何东西。\n'
        '· 关窗口只是缩到托盘，接收不中断；托盘右键可开关「开机自动启动」。\n'
        '· 设置 → 传完再校验文件：慢一些，但能查出读盘、写盘层面的错误。\n\n'
        '—— 1.5 新增 ——\n'
        '· 文件夹镜像：工具 → 镜像文件夹…，选一对目录，只补新增和改过的文件，适合长期同步。\n'
        '· 命令行：LanSplice.exe send <路径> --to <IP> 可以写进批处理和计划任务；\n'
        '  另有 devices（扫局域网）和 version。不带任何参数仍然是图形界面。\n'
        '  退出码 0 = 全成，1 = 有文件没传成（可以重跑，断点会接上），2 = 没开始。\n'
        '  连不上时会说清是「对端没开」还是「不在同一个路由器下」，不再只说 timed out。',
        "① Open the app on both machines; the pairing code shows on the left.\n② Make the two codes match:\n   click 'Copy code', then on the other machine click 'Enter peer code' and paste.\n③ Tools → Find devices again, select the peer.\n④ Drag files or folders into the dashed box (or use 'Choose files/folder').\n⑤ Click '① Send to peer'.\n\nFiles land in the peer's receive folder (default E:\\_xfer) with the folder structure intact.\nFiles with the same name and size are skipped, never re-sent.\n\nIf the peer can't find this machine the first time, click Security → Allow in firewall once.\n\n"
        "—— New in 1.4 ——\n"
        "· Resume: if a transfer breaks, press Send again and it continues from where it stopped.\n"
        "· No silent overwrite: an existing file with the same name becomes 'xxx (2).ext'.\n"
        "· Send text: Ctrl+Shift+V pushes the local clipboard to the peer.\n"
        "· Phone transfer: File → Phone transfer, scan the QR code with a phone browser.\n"
        "· Closing the window only minimises to the tray; receiving keeps running.\n"
        "· Settings → verify after transfer: slower, but catches disk-level errors.\n\n"
        "—— New in 1.5 ——\n"
        "· Folder mirror: Tools → Mirror a folder…; pick a pair of folders and only new or changed files are copied.\n"
        "· Command line: LanSplice.exe send <path> --to <IP> for batch files and scheduled tasks;\n"
        "  plus devices (scan the LAN) and version. No arguments still opens the GUI.\n"
        "  Exit codes: 0 = all done, 1 = some files failed (safe to rerun, resume picks up), 2 = never started.\n"
        "  A failed connection says whether the peer is closed or just not on the same router,\n"
        "  instead of only 'timed out'.",
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
        'Allow in firewall again',
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
        '规则绑的是旧版本，本版可能被拦',
        'Rule points at an older exe — this build may be blocked',
    ),
    "g384": (
        '换了新版本，防火墙要重新放行',
        'New version — the firewall rule needs updating',
    ),
    "g385": (
        'Windows 的防火墙规则是按 exe 的完整路径记的。\n\n'
        '现在是 v%s，路径和上一版不一样，旧规则管不到它 —— '
        '这正是「昨天还好的，今天连不上」的常见原因。\n\n'
        '要现在重新放行吗？（只改本机的入站规则，只对局域网地址开放）',
        'Windows firewall rules are bound to the full path of the exe.\n\n'
        'You are now on v%s, a different path from the previous build, so the old '
        'rule no longer covers it — a common cause of "it worked yesterday".\n\n'
        'Re-allow it now? (inbound only, LAN addresses only)',
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
