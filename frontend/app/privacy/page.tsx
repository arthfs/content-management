const CONTACT = process.env.NEXT_PUBLIC_CONTACT_EMAIL || "the app owner";

export const metadata = { title: "Privacy Policy" };

export default function PrivacyPage() {
  return (
    <main style={{ maxWidth: 720 }}>
      <h1>Privacy Policy</h1>
      <p>Last updated: November 2026</p>

      <h2>1. What we collect</h2>
      <ul>
        <li>Account data: name, email and a hashed password (if sign-in is enabled).</li>
        <li>Profile preferences: timezone and audience age group, used to suggest posting times.</li>
        <li>Videos, titles and captions you upload or schedule.</li>
        <li>
          TikTok connection data: your TikTok open ID and the OAuth access and refresh tokens needed to post for
          you. Tokens are stored server-side and never shown in the browser.
        </li>
        <li>Post status and basic video metrics returned by TikTok for videos posted through this app.</li>
      </ul>

      <h2>2. How we use it</h2>
      <p>
        Only to provide the service: connecting your TikTok account, publishing and scheduling the videos you
        choose, showing post status and metrics, and suggesting posting times and content ideas. We do not sell your
        data or use it for advertising.
      </p>

      <h2>3. Sharing</h2>
      <p>
        Your videos and captions are sent to TikTok only when you post. Hosting providers process data on our
        behalf. If AI suggestions are enabled, video titles, captions and metrics may be sent to Google Gemini to
        generate them.
      </p>

      <h2>4. Retention and deletion</h2>
      <p>
        We keep your data while your account is active. You can delete any video in the app, and you can revoke
        this app&apos;s access in TikTok under Settings and privacy, Security &amp; permissions, Apps and services.
        To delete your account and all stored data, contact {CONTACT}.
      </p>

      <h2>5. Security</h2>
      <p>Connections use HTTPS. Passwords are hashed and TikTok credentials are kept in server-side storage.</p>

      <h2>6. Contact</h2>
      <p>Privacy questions: {CONTACT}.</p>

      <p><a href="/terms">Terms of Service</a></p>
    </main>
  );
}
