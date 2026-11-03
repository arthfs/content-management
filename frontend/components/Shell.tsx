"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getToken, setToken } from "@/lib/api";

export default function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!getToken()) router.replace("/login");
    else setReady(true);
  }, [router]);
  if (!ready) return null;
  return (
    <>
      <nav>
        <strong>Content Manager</strong>
        <Link href="/">Dashboard</Link>
        <Link href="/videos">Videos</Link>
        <Link href="/settings">Settings</Link>
        <span style={{ flex: 1 }} />
        <button className="secondary" onClick={() => { setToken(null); router.replace("/login"); }}>
          Sign out
        </button>
      </nav>
      <main>{children}</main>
    </>
  );
}
