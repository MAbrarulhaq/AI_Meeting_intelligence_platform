const YEAR = new Date().getFullYear();

function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-footer-inner">
        <div className="site-footer-brand">
          <span className="site-footer-logo">Meridian</span>
          <p>Turn meeting recordings into a transcript, summary, and searchable record.</p>
        </div>

        <div className="site-footer-col">
          <span className="site-footer-col-title">Product</span>
          <a href="#capabilities-heading">Capabilities</a>
          <a href="#workflow-heading">How it works</a>
          <a href="#preview-heading">Preview</a>
        </div>

        <div className="site-footer-col">
          <span className="site-footer-col-title">Resources</span>
          <a href="#" onClick={(e) => e.preventDefault()}>
            Documentation
          </a>
          <a href="#" onClick={(e) => e.preventDefault()}>
            Support
          </a>
        </div>

        <div className="site-footer-col">
          <span className="site-footer-col-title">Company</span>
          <a href="#" onClick={(e) => e.preventDefault()}>
            Privacy
          </a>
          <a href="#" onClick={(e) => e.preventDefault()}>
            Terms
          </a>
        </div>
      </div>
      <div className="site-footer-bottom">© {YEAR} Meridian. All rights reserved.</div>
    </footer>
  );
}

export default Footer;
