# Build docx without Word COM
$ErrorActionPreference = 'Stop'
$desktop = [Environment]::GetFolderPath('Desktop')

function Escape-Xml([string]$t) {
    return $t.Replace('&','&amp;').Replace('<','&lt;').Replace('>','&gt;').Replace('"','&quot;')
}

function New-DocxParagraph([string]$text, [string]$style = 'Normal') {
    $esc = Escape-Xml $text
    if ($style -eq 'Title') {
        return "<w:p><w:pPr><w:pStyle w:val=`"Title`"/><w:spacing w:after=`"200`"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val=`"44`"/><w:rFonts w:ascii=`"Microsoft YaHei`" w:eastAsia=`"Microsoft YaHei`"/></w:rPr><w:t xml:space=`"preserve`">$esc</w:t></w:r></w:p>"
    }
    if ($style -eq 'Heading1') {
        return "<w:p><w:pPr><w:pStyle w:val=`"Heading1`"/><w:spacing w:before=`"240`" w:after=`"120`"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val=`"28`"/><w:rFonts w:ascii=`"Microsoft YaHei`" w:eastAsia=`"Microsoft YaHei`"/></w:rPr><w:t xml:space=`"preserve`">$esc</w:t></w:r></w:p>"
    }
    if ($style -eq 'Heading2') {
        return "<w:p><w:pPr><w:pStyle w:val=`"Heading2`"/><w:spacing w:before=`"160`" w:after=`"80`"/></w:pPr><w:r><w:rPr><w:b/><w:sz w:val=`"24`"/><w:rFonts w:ascii=`"Microsoft YaHei`" w:eastAsia=`"Microsoft YaHei`"/></w:rPr><w:t xml:space=`"preserve`">$esc</w:t></w:r></w:p>"
    }
    if ($style -eq 'Bullet') {
        return "<w:p><w:pPr><w:pStyle w:val=`"ListParagraph`"/><w:numPr><w:ilvl w:val=`"0`"/><w:numId w:val=`"1`"/></w:numPr><w:spacing w:after=`"60`"/></w:pPr><w:r><w:rPr><w:sz w:val=`"22`"/><w:rFonts w:ascii=`"Microsoft YaHei`" w:eastAsia=`"Microsoft YaHei`"/></w:rPr><w:t xml:space=`"preserve`">$esc</w:t></w:r></w:p>"
    }
    return "<w:p><w:pPr><w:spacing w:after=`"80`"/></w:pPr><w:r><w:rPr><w:sz w:val=`"22`"/><w:rFonts w:ascii=`"Microsoft YaHei`" w:eastAsia=`"Microsoft YaHei`"/></w:rPr><w:t xml:space=`"preserve`">$esc</w:t></w:r></w:p>"
}

function New-DocxTable($rows) {
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders><w:top w:val="single" w:sz="4"/><w:left w:val="single" w:sz="4"/><w:bottom w:val="single" w:sz="4"/><w:right w:val="single" w:sz="4"/><w:insideH w:val="single" w:sz="4"/><w:insideV w:val="single" w:sz="4"/></w:tblBorders></w:tblPr>')
    for ($ri = 0; $ri -lt $rows.Count; $ri++) {
        [void]$sb.Append('<w:tr>')
        for ($ci = 0; $ci -lt 2; $ci++) {
            $cell = Escape-Xml $rows[$ri][$ci]
            $bold = if ($ri -eq 0) { '<w:b/>' } else { '' }
            [void]$sb.Append("<w:tc><w:tcPr><w:tcW w:w=`"2500`" w:type=`"pct`"/></w:tcPr><w:p><w:r><w:rPr>$bold<w:rFonts w:ascii=`"Microsoft YaHei`" w:eastAsia=`"Microsoft YaHei`"/><w:sz w:val=`"22`"/></w:rPr><w:t xml:space=`"preserve`">$cell</w:t></w:r></w:p></w:tc>")
        }
        [void]$sb.Append('</w:tr>')
    }
    [void]$sb.Append('</w:tbl>')
    return $sb.ToString()
}

function Save-Docx([string]$path, [string[]]$parts) {
    $temp = Join-Path $env:TEMP ("geo_docx_" + [guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $temp | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $temp '_rels') | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $temp 'word\_rels') | Out-Null

    $body = ($parts -join '')
    $documentXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
$body
<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
</w:body>
</w:document>
"@

    $contentTypes = @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
'@

    $rels = @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
'@

    $docRels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'

    [IO.File]::WriteAllText((Join-Path $temp '[Content_Types].xml'), $contentTypes, [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $temp '_rels\.rels'), $rels, [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $temp 'word\document.xml'), $documentXml, [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $temp 'word\_rels\document.xml.rels'), $docRels, [Text.UTF8Encoding]::new($false))

    if (Test-Path $path) { Remove-Item $path -Force }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::CreateFromDirectory($temp, $path)
    Remove-Item $temp -Recurse -Force
}

# ===== PRD =====
$prd = @()
$prd += New-DocxParagraph 'GEO 智能品牌平台 — 产品需求文档（技术版）' 'Title'
$prd += New-DocxParagraph '版本 V4.1 | 2026-07-04 | 读者：研发 / 架构 / 测试 | MVP：生美'
$prd += New-DocxParagraph '一、产品定义' 'Heading1'
$prd += New-DocxParagraph 'GEO（生成式引擎优化）= 让豆包/DeepSeek/Kimi/文心等 AI 引用、采信企业真实品牌信息。'
$prd += New-DocxParagraph '价值公式：内容价值 ≈ 信息增量 × 品牌信任度'
$prd += New-DocxParagraph '做：知识库零幻觉、先选 AI 测信源、按顾客场景写内容、监测迭代' 'Bullet'
$prd += New-DocxParagraph '不做：软文铺量、保证第一、虚构品牌、刷好评' 'Bullet'
$prd += New-DocxParagraph '二、用户旅程（三舱 · 2 次确认）' 'Heading1'
$prd += New-DocxTable @(@('舱','用户操作'),@('舱1 懂我','开店向导 → 开始分析'),@('舱2 定方案','方案包确认 → 草稿审通过'),@('舱3 出结果','发布 → 效果舱 → 策略建议'))
$prd += New-DocxParagraph '人闸门：① 方案包「确认并生成」  ② 草稿「通过」'
$prd += New-DocxParagraph '铁律：无事实不发布 | 条数=场景数(≤5) | 临界只出草案'
$prd += New-DocxParagraph '三、系统管道' 'Heading1'
$prd += New-DocxParagraph '录入 → 信源诊断 → 痛点/词库 → 画像/竞品 → 方案包 → 生成 → 双审 → 发布 → 监测 → 效果舱'
$prd += New-DocxParagraph '方案包五区块' 'Heading2'
$prd += New-DocxTable @(@('区块','内容'),@('A 画像','确认顾客画像与布局'),@('B 竞品','确认差异化'),@('C 场景','勾选2-5个顾客问题'),@('D 渠道','信源权重与承接场景数'),@('E 展开','词库、知识库更新提示'))
$prd += New-DocxParagraph '四、核心规则' 'Heading1'
$prd += New-DocxParagraph 'Fact 可发布：NAP、项目、案例、FAQ' 'Bullet'
$prd += New-DocxParagraph 'Signal 不可发布：聊天/评价粘贴' 'Bullet'
$prd += New-DocxParagraph '生成链：fact_refs → kb_fetch → LLM → fact_verify' 'Bullet'
$prd += New-DocxParagraph '薄库门槛：≥2 项目且 ≥3 FAQ 才能确认生成' 'Bullet'
$prd += New-DocxParagraph '生产单元：1 场景 × 1 渠道 × 1 Skill' 'Bullet'
$prd += New-DocxParagraph '五、技术选型' 'Heading1'
$prd += New-DocxTable @(@('层','选型'),@('前端','Vue3 + TS + Element Plus'),@('后端','Python FastAPI + Pydantic v2'),@('数据','PostgreSQL + Redis + Celery + Faiss'),@('Agent','jobs + LangGraph + ReAct'),@('LLM','Gateway + 四引擎'),@('可观测','Sentry + LangSmith'))
$prd += New-DocxParagraph '六、MVP-A 首发范围' 'Heading1'
$prd += New-DocxTable @(@('项','范围'),@('诊断','主攻 AI 全量'),@('内容','2 个场景'),@('发布','托管页 + 1 渠道 SEMI'),@('监测','主攻 AI 一轮'))
$prd += New-DocxParagraph '七、关键接口' 'Heading1'
$prd += New-DocxParagraph 'POST /onboarding/run | GET/POST /strategy-pack/* | GET /content-drafts | GET /outcomes' 'Bullet'
$prd += New-DocxParagraph '八、验收要点' 'Heading1'
$prd += New-DocxParagraph '1 店全流程跑通；事实可追溯；两次人审；跨租户 403' 'Bullet'
$prd += New-DocxParagraph '九、版本：MVP → V1.1(归因/trust) → V2(B2B)' 'Heading1'

$p1 = Join-Path $desktop 'GEO-PRD-技术版.docx'
Save-Docx $p1 $prd

# ===== Customer =====
$c = @()
$c += New-DocxParagraph 'GEO 产品介绍' 'Title'
$c += New-DocxParagraph '面向：皮肤管理 / 生活美容门店负责人 | V4.1 | 2026-07-04'
$c += New-DocxParagraph '一、您遇到的问题' 'Heading1'
$c += New-DocxParagraph '顾客问 AI：附近哪家皮肤管理靠谱？AI 没提到您，顾客就想不到您。'
$c += New-DocxParagraph '二、我们做什么' 'Heading1'
$c += New-DocxParagraph '整理 AI 能引用真实资料：选 AI、测信源、按顾客问题写内容、看效果。首版看提及、引用、店页访问。不是刷好评、不保证第一。'
$c += New-DocxParagraph '三、您只需 3 步' 'Heading1'
$c += New-DocxParagraph '第 1 步：填店信息，点「开始分析」（约十几到几十分钟）' 'Bullet'
$c += New-DocxParagraph '第 2 步：看方案包，勾选 2-3 个问题，确认生成，审一遍文案' 'Bullet'
$c += New-DocxParagraph '第 3 步：官网自动发；小红书/知乎给文案包；效果舱看数据' 'Bullet'
$c += New-DocxParagraph '四、系统帮您什么' 'Heading1'
$c += New-DocxTable @(@('价值','说明'),@('选主攻 AI','方案围绕您的选择'),@('先测再写','看 AI 爱引哪类网站'),@('按问题写','每问题 1 条内容'),@('合规','避开违规词'),@('效果','提及、引用、访问'))
$c += New-DocxParagraph '五、发到哪里' 'Heading1'
$c += New-DocxTable @(@('渠道','我们/您'),@('官网页','自动/不用管'),@('小红书知乎','文案包/您复制'),@('点评美团','指引+稿/您改'))
$c += New-DocxParagraph '六、请您准备' 'Heading1'
$c += New-DocxTable @(@('必填','说明'),@('NAP','店名地址电话'),@('≥2 项目','含价格'),@('≥3 FAQ','常见问答'),@('≥5 聊天评价','去掉手机号'),@('2-3 竞品','店名'),@('主攻 AI','如豆包'))
$c += New-DocxParagraph '七、费用：标准包 3 问题 + 2 AI 监测/月；加购按问题条数' 'Heading1'
$c += New-DocxParagraph '八、不是什么：不保证第一、不刷好评、不堆篇数' 'Heading1'
$c += New-DocxParagraph '九、多久见效：方案约1天 | 内容数小时 | 发布24h可测 | 趋势4-8周' 'Heading1'

$p2 = Join-Path $desktop 'GEO-产品介绍-客户版.docx'
Save-Docx $p2 $c

Write-Output $p1
Write-Output $p2
