const CONTACT = process.env.NEXT_PUBLIC_CONTACT_EMAIL || "the app owner";

export const metadata = { title: "Terms of Service" };

export default function TermsPage() {
  return (
    <main style={{ maxWidth: 720 }}>
      <h1>Terms of Service</h1>
      <p>Last updated: November 2026</p>

      <h2>1. The service</h2>
      <p>
        This app helps you upload videos, schedule them and publish them to your own TikTok account at a
        suggested best time. It uses the TikTok Content Posting API after you connect your account.
      </p>

      <h2>2. Your account and content</h2>
      <p>
        You are responsible for your account and for the videos, titles and captions you post. You must own or
        have the rights to everything you upload, including any music, and you must follow TikTok&apos;s{" "}
        <a href="https://www.tiktok.com/legal/page/global/terms-of-service/en">Terms of Service</a>,{" "}
        <a href="https://www.tiktok.com/community-guidelines">Community Guidelines</a> and{" "}
        <a href="https://www.tiktok.com/legal/page/global/music-usage-confirmation/en">Music Usage Confirmation</a>.
        If you promote a brand, you must disclose it and follow the{" "}
        <a href="https://www.tiktok.com/legal/page/global/bc-policy/en">Branded Content Policy</a>.
      </p>

      <h2>3. Posting on your behalf</h2>
      <p>
        We only post a video after you explicitly choose to post or schedule it. We never add watermarks, logos or
        promotional text to your videos or captions. You can revoke this app&apos;s access at any time in TikTok
        (Settings and privacy, Security &amp; permissions, Apps and services), which stops all further posting.
      </p>

      <h2>4. Acceptable use</h2>
      <p>
        Do not use the service for unlawful, misleading, infringing or harmful content, or to attempt to bypass
        TikTok&apos;s rules or rate limits.
      </p>

      <h2>5. No guarantees</h2>
      <p>
        Best-time suggestions are estimates and do not guarantee views or engagement. The service is provided
        &quot;as is&quot;, and posting can fail because of TikTok-side limits or outages.
      </p>

      <h2>6. Termination</h2>
      <p>
        You may stop using the service and request deletion of your data at any time. We may suspend accounts that
        violate these terms.
      </p>

      <h2>7. Contact</h2>
      <p>Questions about these terms: {CONTACT}.</p>

      <p><a href="/privacy">Privacy Policy</a></p>
    </main>
  );
}
