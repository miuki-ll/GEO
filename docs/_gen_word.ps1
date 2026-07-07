$desktop = [Environment]::GetFolderPath('Desktop')
$word = New-Object -ComObject Word.Application
$word.Visible = $false

function Add-Title($doc, $text) {
    $p = $doc.Paragraphs.Add()
    $p.Range.Text = $text
    $p.Range.Font.Size = 22
    $p.Range.Font.Bold = $true
    $p.Range.Font.Name = 'Microsoft YaHei'
    $p.Format.SpaceAfter = 6
}

function Add-H1($doc, $text) {
    $p = $doc.Paragraphs.Add()
    $p.Range.Text = $text
    $p.Range.Font.Size = 14
    $p.Range.Font.Bold = $true
    $p.Range.Font.Name = 'Microsoft YaHei'
    $p.Format.SpaceBefore = 12
    $p.Format.SpaceAfter = 6
}

function Add-H2($doc, $text) {
    $p = $doc.Paragraphs.Add()
    $p.Range.Text = $text
    $p.Range.Font.Size = 12
    $p.Range.Font.Bold = $true
    $p.Range.Font.Name = 'Microsoft YaHei'
    $p.Format.SpaceBefore = 8
    $p.Format.SpaceAfter = 4
}

function Add-P($doc, $text) {
    $p = $doc.Paragraphs.Add()
    $p.Range.Text = $text
    $p.Range.Font.Size = 11
    $p.Range.Font.Name = 'Microsoft YaHei'
    $p.Format.SpaceAfter = 4
}

function Add-Bullet($doc, $text) {
    $p = $doc.Paragraphs.Add()
    $p.Range.Text = $text
    $p.Range.ListFormat.ApplyBulletDefault() | Out-Null
    $p.Range.Font.Size = 11
    $p.Range.Font.Name = 'Microsoft YaHei'
    $p.Format.SpaceAfter = 2
}

function Add-Table2Col($doc, $rows) {
    $n = $rows.Count
    $t = $doc.Tables.Add($doc.Paragraphs.Add().Range, $n, 2)
    $t.Borders.Enable = $true
    for ($i = 0; $i -lt $n; $i++) {
        $t.Cell($i+1,1).Range.Text = $rows[$i][0]
        $t.Cell($i+1,2).Range.Text = $rows[$i][1]
        if ($i -eq 0) { $t.Rows(1).Range.Font.Bold = $true }
    }
    $doc.Paragraphs.Add() | Out-Null
}

# ===== PRD =====
$d1 = $word.Documents.Add()
Add-Title $d1 'GEO - PRD (Technical)'
Add-P $d1 'Version V4.1 | Date 2026-07-04 | Audience: Dev / QA / Architecture'
Add-P $d1 'Industry MVP: beauty_local | Full spec: Desktop\GEO\v4\'

Add-H1 $d1 '1. Product Definition'
Add-P $d1 'GEO = Help AI (Doubao, DeepSeek, Kimi, Wenxin) cite your real brand facts.'
Add-P $d1 'Value = Information Increment x Brand Trust. NOT: spam content, rank guarantee, fake brands.'

Add-H1 $d1 '2. User Journey (3 cabins, 2 gates)'
Add-Table2Col $d1 @(
    @('Cabin','User Action'),
    @('Cabin1 Know Me','Onboarding form -> Start Analysis'),
    @('Cabin2 Plan','Strategy Pack confirm -> Draft approve'),
    @('Cabin3 Results','Publish -> Outcome dashboard -> Strategy suggestion')
)
Add-P $d1 'Human gates: (1) Confirm & Generate (2) Approve drafts'
Add-P $d1 'Rules: No Fact no publish | Count = scenario count (max 5) | Threshold triggers draft only'

Add-H1 $d1 '3. System Pipeline'
Add-P $d1 'onboarding -> diagnose -> pain/keyword -> persona -> competitor -> strategy pack -> GAP -> PLAN -> generate -> machine review -> human review -> publish -> monitor -> outcomes'

Add-H2 $d1 'Strategy Pack Blocks'
Add-Table2Col $d1 @(
    @('Block','Content'),
    @('A Persona','Confirm buyer persona + layout'),
    @('B Competitor','Confirm differentiation'),
    @('C Scenario','Select 2-5 customer questions (production unit)'),
    @('D Channel','Source weight + scenario slots per channel'),
    @('E Expand','Keywords (monitoring), KB freshness alert')
)

Add-H1 $d1 '4. KB and Content Rules'
Add-Bullet $d1 'Fact layer (publishable): NAP, services, cases, FAQs'
Add-Bullet $d1 'Signal layer: RawInputs (chat/reviews) - not directly publishable'
Add-Bullet $d1 'Generation chain: fact_refs -> kb_fetch -> LLM -> fact_verify'
Add-Bullet $d1 'Thin KB gate: need >=2 services AND >=3 FAQs to enable Confirm'

Add-H1 $d1 '5. Tech Stack'
Add-Table2Col $d1 @(
    @('Layer','Choice'),
    @('Frontend','Vue3 + TS + Element Plus'),
    @('Backend','Python 3.11+ / FastAPI / Pydantic v2'),
    @('Data','PostgreSQL / Redis / Celery / Faiss / OSS'),
    @('Agent','L1 jobs + L2 LangGraph + L3 ReAct Harness'),
    @('LLM','Gateway + 4 EngineAdapters'),
    @('Observability','Sentry + LangSmith + agent_traces')
)

Add-H1 $d1 '6. MVP-A Launch Scope'
Add-Table2Col $d1 @(
    @('Item','MVP-A'),
    @('Diagnose','Primary engine full; secondary optional'),
    @('Content','2 scenarios (standard pack: 3)'),
    @('Publish','Hosted page AUTO + 1 channel SEMI'),
    @('Monitor','Primary engine Core 1 round + scenario in Core subset')
)

Add-H1 $d1 '7. Key APIs'
Add-Bullet $d1 'POST /onboarding/run'
Add-Bullet $d1 'GET/POST /strategy-pack/draft|confirm'
Add-Bullet $d1 'GET /content-drafts | POST bulk-approve'
Add-Bullet $d1 'GET /outcomes'

Add-H1 $d1 '8. Acceptance (summary)'
Add-Bullet $d1 'Full flow: onboarding -> pack -> FAQ + 1 channel -> hosted page -> monitor'
Add-Bullet $d1 'fact_refs traceable; compliance block; tenant isolation; 2 human gates'
Add-Bullet $d1 'SEMI export pack; cross-tenant access returns 403'

Add-H1 $d1 '9. Roadmap'
Add-Bullet $d1 'MVP: 3 cabins + scenario + kb_fetch + Core/Probe'
Add-Bullet $d1 'V1.1: trust_asset, ConsultLog, full scenario monitoring'
Add-Bullet $d1 'V2: B2B pack, adapt_engine multi-format'

$p1 = Join-Path $desktop 'GEO-PRD-Technical.docx'
if (Test-Path $p1) { Remove-Item $p1 -Force }
$d1.SaveAs([ref]$p1, [ref]16)
$d1.Close()

# ===== Customer =====
$d2 = $word.Documents.Add()
Add-Title $d2 'GEO Product Introduction'
Add-P $d2 'For: Beauty / Skin Care Store Owners | V4.1 | 2026-07-04'

Add-H1 $d2 '1. Your Problem'
Add-P $d2 'Customers ask AI: Which skin care shop nearby is good? AI does not mention you - they never think of you.'

Add-H1 $d2 '2. What We Do'
Add-P $d2 'Organize real store info AI can cite. Pick your AI, test sources, write by real customer questions, track results.'
Add-P $d2 'Focus: AI mentions, your page cited, store page visits. NOT: fake reviews, rank guarantee, spam posts.'

Add-H1 $d2 '3. Three Steps'
Add-H2 $d2 'Step 1: Tell us about your store'
Add-Bullet $d2 'Pick main AI (e.g. Doubao)'
Add-Bullet $d2 'Store info, services, competitors, customer Q&A'
Add-Bullet $d2 'Click Start Analysis (about 15-30 min)'

Add-H2 $d2 'Step 2: Review plan and approve content'
Add-Bullet $d2 'One-page plan: which questions to answer, where to publish'
Add-Bullet $d2 'Pick 2-3 questions, click Confirm & Generate'
Add-Bullet $d2 'If FAQ/projects too few, system asks you to add first'
Add-Bullet $d2 'You review drafts (system checks facts and compliance)'

Add-H2 $d2 'Step 3: Publish and see results'
Add-Bullet $d2 'Store page auto-published'
Add-Bullet $d2 'XHS/Zhihu: standard copy pack for you to paste'
Add-Bullet $d2 'Dashboard: AI mentions, citations, page visits'

Add-H1 $d2 '4. What You Get'
Add-Table2Col $d2 @(
    @('Value','Description'),
    @('Pick main AI','Plan fits your choice'),
    @('Test then write','See what AI cites before publishing'),
    @('By question not volume','1 question = 1 content piece'),
    @('Compliance','Block illegal ad words'),
    @('Results + tips','Mentions, citations, next-step suggestions')
)

Add-H1 $d2 '5. Where to Publish'
Add-Table2Col $d2 @(
    @('Channel','Us / You'),
    @('Hosted store page','Auto / Almost nothing'),
    @('XHS, Zhihu','Copy pack / You paste'),
    @('Dianping, Meituan','Guide + draft / You follow steps')
)

Add-H1 $d2 '6. Please Prepare'
Add-Table2Col $d2 @(
    @('Required','Note'),
    @('Name, address, phone','Basic NAP'),
    @('>=2 services','With price or duration'),
    @('>=3 FAQs','Common Q&A'),
    @('>=5 chat/review snippets','Remove customer phone numbers'),
    @('2-3 competitors','Names only'),
    @('Main AI','e.g. Doubao')
)

Add-H1 $d2 '7. Pricing (draft)'
Add-Bullet $d2 'Standard: 3 customer questions + 2 AI monitoring / month'
Add-Bullet $d2 'Add-on: by question count, not 5 XHS posts'
Add-Bullet $d2 'Price TBD'

Add-H1 $d2 '8. What We Are NOT'
Add-Bullet $d2 'No rank guarantee'
Add-Bullet $d2 'No fake reviews or fake brands'
Add-Bullet $d2 'No keyword stuffing'

Add-H1 $d2 '9. Timeline'
Add-P $d2 'Plan+diagnose: ~1 day | Content: hours after confirm | First check: ~24h after publish | Trend: 4-8 weeks'

$p2 = Join-Path $desktop 'GEO-Product-Customer.docx'
if (Test-Path $p2) { Remove-Item $p2 -Force }
$d2.SaveAs([ref]$p2, [ref]16)
$d2.Close()

$word.Quit()
Write-Output $p1
Write-Output $p2
