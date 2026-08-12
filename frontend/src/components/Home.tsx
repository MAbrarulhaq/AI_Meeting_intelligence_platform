import Button from "./ui/Button";
import { Card, Badge } from "./ui/Card";
import WaveformMark from "./ui/WaveformMark";
import Footer from "./layout/Footer";

interface HomeProps {
  onGetStarted: () => void;
  onSignIn: () => void;
}

const CAPABILITIES = [
  {
    title: "Transcription",
    body: "Every recording is transcribed automatically, with timestamps down to the segment.",
  },
  {
    title: "Speaker identification",
    body: "Diarization separates the transcript by speaker, so you know who said what.",
  },
  {
    title: "AI summaries",
    body: "A concise summary of what the meeting actually covered — no re-listening required.",
  },
  {
    title: "Action item extraction",
    body: "Tasks mentioned in conversation are pulled out with an owner and a deadline, where stated.",
  },
  {
    title: "Decision & deadline tracking",
    body: "Decisions and dates are listed separately from the transcript, so they're easy to reference.",
  },
  {
    title: "Semantic search & AI assistant",
    body: "Ask a question in plain language and get an answer sourced from the actual transcript.",
  },
];

const WORKFLOW = [
  { title: "Meeting recording", body: "Upload an audio file from any meeting." },
  { title: "Transcription", body: "Speech becomes text, segment by segment." },
  { title: "Speaker diarization", body: "Segments are attributed to individual speakers." },
  { title: "AI analysis", body: "Summary, action items, decisions, and deadlines are extracted." },
  { title: "Search & chat", body: "Everything is indexed and ready to query." },
];

const TRUST = [
  { title: "Skip the re-watch", body: "Read what happened instead of scrubbing through a recording." },
  { title: "Nothing falls through", body: "Action items are recorded the moment they're spoken." },
  { title: "Find decisions fast", body: "Every decision is separated from the transcript, not buried in it." },
  { title: "Ask, don't search", body: "Question a meeting in plain language and get a sourced answer." },
];

function Home({ onGetStarted, onSignIn }: HomeProps) {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <span className="landing-nav-name">Meridian</span>
        <div className="landing-nav-actions">
          <Button variant="ghost" size="sm" onClick={onSignIn}>
            Sign in
          </Button>
          <Button variant="primary" size="sm" onClick={onGetStarted}>
            Get started
          </Button>
        </div>
      </nav>

      <header className="hero">
        <div>
          <span className="hero-eyebrow">meeting intelligence platform</span>
          <h1>Turn recordings into a record you can search.</h1>
          <p className="hero-sub">
            Meridian transcribes your meetings, identifies who said what, and pulls out the
            summary, decisions, and action items — so any answer is a search away, not a
            re-listen.
          </p>
          <div className="hero-actions">
            <Button onClick={onGetStarted}>Get started</Button>
            <Button variant="secondary" onClick={onSignIn}>
              Sign in
            </Button>
          </div>
        </div>
        <WaveformMark className="hero-mark" />
      </header>

      <section className="section" aria-labelledby="capabilities-heading">
        <div className="section-head">
          <span className="section-eyebrow">What it does</span>
          <h2 id="capabilities-heading">Six things happen to every meeting you upload.</h2>
        </div>
        <div className="capability-grid">
          {CAPABILITIES.map((c) => (
            <Card key={c.title} className="capability-card">
              <h3>{c.title}</h3>
              <p>{c.body}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className="section" aria-labelledby="workflow-heading">
        <div className="section-head">
          <span className="section-eyebrow">How it works</span>
          <h2 id="workflow-heading">From recording to searchable record.</h2>
        </div>
        <Card>
          <div className="workflow">
            {WORKFLOW.map((step, index) => (
              <div className="workflow-step" key={step.title}>
                <span className="workflow-index">{String(index + 1).padStart(2, "0")}</span>
                <h4>{step.title}</h4>
                <p>{step.body}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>

      <section className="section" aria-labelledby="preview-heading">
        <div className="section-head">
          <span className="section-eyebrow">Your workspace</span>
          <h2 id="preview-heading">What a meeting looks like once it's processed.</h2>
        </div>
        <Card className="preview-panel">
          <div className="preview-panel-head">
            <h3>Recent meetings</h3>
            <Badge tone="accent">example</Badge>
          </div>
          <div className="preview-meeting">
            <div>
              <p className="preview-meeting-name">product-sync-aug-04.wav</p>
              <span className="preview-meeting-meta">Aug 4, 2026 · 34m</span>
            </div>
            <p className="preview-meeting-summary">
              Team reviewed the launch checklist and agreed to push the beta date by one week
              pending QA sign-off.
            </p>
            <div className="preview-meeting-counts">
              <Badge>3 action items</Badge>
              <Badge>2 decisions</Badge>
            </div>
          </div>
          <div className="preview-meeting">
            <div>
              <p className="preview-meeting-name">client-onboarding-call.wav</p>
              <span className="preview-meeting-meta">Aug 1, 2026 · 22m</span>
            </div>
            <p className="preview-meeting-summary">
              Walked the client through account setup; follow-up scheduled to confirm data
              migration timeline.
            </p>
            <div className="preview-meeting-counts">
              <Badge>1 action item</Badge>
              <Badge>1 deadline</Badge>
            </div>
          </div>
        </Card>
      </section>

      <section className="section" aria-labelledby="trust-heading">
        <div className="section-head">
          <span className="section-eyebrow">Why it's worth doing</span>
          <h2 id="trust-heading">What changes once meetings are searchable.</h2>
        </div>
        <div className="trust-grid">
          {TRUST.map((t) => (
            <div className="trust-item" key={t.title}>
              <h4>{t.title}</h4>
              <p>{t.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="final-cta">
        <h2>Upload your first meeting.</h2>
        <p>Create an account and see what your next recording turns into.</p>
        <div className="final-cta-actions">
          <Button onClick={onGetStarted}>Get started</Button>
        </div>
      </section>

      <Footer />
    </div>
  );
}

export default Home;
