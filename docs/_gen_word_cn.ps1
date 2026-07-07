# UTF-8
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8
$desktop = [Environment]::GetFolderPath('Desktop')
$word = New-Object -ComObject Word.Application
$word.Visible = $false

function W-Title($d,$t){$p=$d.Paragraphs.Add();$p.Range.Text=$t;$p.Range.Font.Size=22;$p.Range.Font.Bold=$true;$p.Range.Font.Name='Microsoft YaHei';$p.Format.SpaceAfter=6}
function W-H1($d,$t){$p=$d.Paragraphs.Add();$p.Range.Text=$t;$p.Range.Font.Size=14;$p.Range.Font.Bold=$true;$p.Range.Font.Name='Microsoft YaHei';$p.Format.SpaceBefore=12;$p.Format.SpaceAfter=6}
function W-H2($d,$t){$p=$d.Paragraphs.Add();$p.Range.Text=$t;$p.Range.Font.Size=12;$p.Range.Font.Bold=$true;$p.Range.Font.Name='Microsoft YaHei';$p.Format.SpaceBefore=8;$p.Format.SpaceAfter=4}
function W-P($d,$t){$p=$d.Paragraphs.Add();$p.Range.Text=$t;$p.Range.Font.Size=11;$p.Range.Font.Name='Microsoft YaHei';$p.Format.SpaceAfter=4}
function W-B($d,$t){$p=$d.Paragraphs.Add();$p.Range.Text=$t;$p.Range.ListFormat.ApplyBulletDefault()|Out-Null;$p.Range.Font.Size=11;$p.Range.Font.Name='Microsoft YaHei';$p.Format.SpaceAfter=2}
function W-T2($d,$rows){$n=$rows.Count;$t=$d.Tables.Add($d.Paragraphs.Add().Range,$n,2);$t.Borders.Enable=$true;for($i=0;$i -lt $n;$i++){$t.Cell($i+1,1).Range.Text=$rows[$i][0];$t.Cell($i+1,2).Range.Text=$rows[$i][1];if($i -eq 0){$t.Rows(1).Range.Font.Bold=$true}};$d.Paragraphs.Add()|Out-Null}

$d1=$word.Documents.Add()
W-Title $d1 'GEO 智能品牌平台 — 产品需求文档（技术版）'
W-P $d1 '版本 V4.1 | 日期 2026-07-04 | 读者：研发 / 架构 / 测试'
W-P $d1 'MVP 行业：生美 | 完整规格：Desktop\GEO\v4\'

W-H1 $d1 '一、产品定义'
W-P $d1 'GEO（生成式引擎优化）= 让豆包/DeepSeek/Kimi/文心等 AI 引用、采信企业真实品牌信息。'
W-P $d1 '价值公式：内容价值 = 信息增量 x 品牌信任度'
W-B $d1 '做：知识库零幻觉、先选 AI 测信源、按顾客场景写内容、监测迭代'
W-B $d1 '不做：软文铺量、保证第一、虚构品牌、刷好评'

W-H1 $d1 '二、用户旅程（三舱 · 2 次确认）'
W-T2 $d1 @(
@('舱','用户操作'),
@('舱1 懂我','开店向导提交 - 开始分析'),
@('舱2 定方案','方案包确认 - 草稿审通过'),
@('舱3 出结果','发布 - 效果舱 - 策略建议')
)
W-P $d1 '人闸门：① 方案包「确认并生成」  ② 草稿「通过」'
W-P $d1 '铁律：无事实不发布 | 条数=场景数(最多5) | 监测临界只出草案'

W-H1 $d1 '三、系统管道'
W-P $d1 '录入 - 信源诊断 - 痛点词库 - 画像竞品 - 方案包确认 - 生成 - 机器审 - 人工审 - 发布 - 监测 - 效果舱'

W-H2 $d1 '方案包五区块'
W-T2 $d1 @(
@('区块','内容'),
@('A 画像','确认顾客画像与内容布局'),
@('B 竞品','确认/编辑差异化'),
@('C 场景','勾选2-5个顾客问题(scenario)'),
@('D 渠道','信源权重与各渠道承接场景数'),
@('E 展开','词库(监测辅助)、知识库更新提示')
)

W-H1 $d1 '四、核心规则'
W-B $d1 '知识库 Fact 可发布：店名地址电话、项目、案例、FAQ'
W-B $d1 'Signal 不可直接发布：粘贴的聊天/评价'
W-B $d1 '生成链：fact_refs - kb_fetch - LLM - fact_verify'
W-B $d1 '薄库门槛：至少2个项目且3条FAQ，否则不能点确认生成'
W-B $d1 '生产单元：1个场景 x 1个渠道 x 1个Skill'

W-H1 $d1 '五、技术选型'
W-T2 $d1 @(
@('层','选型'),
@('前端','Vue3 + TypeScript + Element Plus'),
@('后端','Python FastAPI + Pydantic v2'),
@('数据','PostgreSQL + Redis + Celery + Faiss + OSS'),
@('Agent','jobs + LangGraph子图 + ReAct'),
@('LLM','Gateway + 四引擎适配器'),
@('可观测','Sentry + LangSmith + agent_traces')
)

W-H1 $d1 '六、MVP-A 首发范围'
W-T2 $d1 @(
@('项','范围'),
@('诊断','主攻AI全量，次攻可选'),
@('内容','2个场景(标准包3个)'),
@('发布','托管页自动 + 1渠道文案包(SEMI)'),
@('监测','主攻AI一轮 + 场景进监测池')
)

W-H1 $d1 '七、关键接口'
W-B $d1 'POST /onboarding/run'
W-B $d1 'GET /strategy-pack/draft  POST /strategy-pack/confirm'
W-B $d1 'GET /content-drafts  POST bulk-approve'
W-B $d1 'GET /outcomes'

W-H1 $d1 '八、验收要点'
W-B $d1 '1店全流程：向导-方案包-FAQ+1渠道-托管页-监测1轮'
W-B $d1 '事实可追溯、禁词拦截、租户隔离、两次人审'
W-B $d1 '文案包可导出、跨租户访问403'

W-H1 $d1 '九、版本'
W-B $d1 'MVP：三舱 + 场景驱动 + 监测'
W-B $d1 'V1.1：信任资产产线、咨询归因、完整场景监测'
W-B $d1 'V2：B2B行业包、一源多形态内容'

$p1=Join-Path $desktop 'GEO-PRD-技术版.docx'
if(Test-Path $p1){Remove-Item $p1 -Force}
$d1.SaveAs([ref]$p1,[ref]16); $d1.Close()

$d2=$word.Documents.Add()
W-Title $d2 'GEO 产品介绍'
W-P $d2 '面向：皮肤管理 / 生活美容门店负责人 | V4.1 | 2026-07-04'

W-H1 $d2 '一、您遇到的问题'
W-P $d2 '顾客越来越多问 AI：附近哪家皮肤管理靠谱？AI 没提到您，顾客就想不到您。'

W-H1 $d2 '二、我们做什么'
W-P $d2 '帮门店整理 AI 能看懂、能引用的真实资料：先选您关心的 AI，测信源，按顾客真实问题写内容，看效果。'
W-P $d2 '首版看：AI 是否提到您、网页是否被引用、店页有没有人来问。'
W-P $d2 '不是刷好评，不保证第一名，不堆篇数。'

W-H1 $d2 '三、您只需 3 步'
W-H2 $d2 '第1步：告诉我们店的信息'
W-B $d2 '勾选最在意的 AI（如豆包）'
W-B $d2 '填写店名、地址、项目、价格、竞品、客户常问'
W-B $d2 '点「开始分析」，约十几到几十分钟'

W-H2 $d2 '第2步：看方案、确认出稿'
W-B $d2 '一页方案包：建议回答哪几个问题、发到哪里'
W-B $d2 '勾选 2-3 个问题，点「确认并生成」'
W-B $d2 '资料不够时请先补 FAQ 和项目'
W-B $d2 '文案出来后您审一遍（系统已查事实和合规）'

W-H2 $d2 '第3步：发布并看效果'
W-B $d2 '官网页可自动发布'
W-B $d2 '小红书/知乎给标准文案包，您复制发布'
W-B $d2 '效果舱看：AI 是否提到、网页是否被引用、店页访问'

W-H1 $d2 '四、系统帮您什么'
W-T2 $d2 @(
@('价值','说明'),
@('选主攻 AI','方案围绕您的选择'),
@('先测再写','看 AI 爱引哪类网站'),
@('按问题写','每个顾客问题1条内容'),
@('合规检查','避开违规广告词'),
@('效果+建议','提及、引用、访问；不好时给建议')
)

W-H1 $d2 '五、发到哪里'
W-T2 $d2 @(
@('渠道','我们 / 您'),
@('平台官网页','自动发 / 几乎不用管'),
@('小红书、知乎','给文案包 / 您复制发布'),
@('点评、美团','给优化稿+指引 / 您按指引改')
)

W-H1 $d2 '六、请您准备'
W-T2 $d2 @(
@('必填','说明'),
@('店名、地址、电话','基本信息'),
@('至少2个项目','含价格或时长'),
@('至少3条FAQ','常见问答'),
@('至少5条聊天或评价','请去掉顾客手机号'),
@('2-3家竞品','店名即可'),
@('主攻 AI','如豆包')
)

W-H1 $d2 '七、费用（初版）'
W-B $d2 '标准包：3个顾客问题 + 2个AI监测 / 月'
W-B $d2 '加购按问题条数，不是小红书5篇'
W-B $d2 '具体单价洽谈中'

W-H1 $d2 '八、不是什么'
W-B $d2 '不保证 AI 排名第一'
W-B $d2 '不刷好评、不虚构品牌'
W-B $d2 '不堆关键词凑篇数'

W-H1 $d2 '九、多久见效'
W-P $d2 '方案约1天 | 内容确认后数小时 | 发布后约24小时可测 | 趋势通常4-8周'

$p2=Join-Path $desktop 'GEO-产品介绍-客户版.docx'
if(Test-Path $p2){Remove-Item $p2 -Force}
$d2.SaveAs([ref]$p2,[ref]16); $d2.Close()

$word.Quit()
Write-Output $p1
Write-Output $p2
