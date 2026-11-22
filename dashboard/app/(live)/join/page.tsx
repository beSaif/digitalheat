"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LogoMark } from "@/components/Logo";

/*
 * Where the QR code on the live screen points. Gives this device a house id (kept in localStorage,
 * so scanning again or reloading brings back the same house) and opens its server page.
 */

const KEY = "dh-live-id";

export default function JoinPage() {
  const router = useRouter();
  useEffect(() => {
    let id = localStorage.getItem(KEY);
    if (!id || !/^p-[a-z0-9]{6}$/.test(id)) {
      id = "p-" + Array.from(crypto.getRandomValues(new Uint8Array(6)), (b) => "abcdefghijkmnpqrstuvwxyz23456789"[b % 32]).join("");
      localStorage.setItem(KEY, id);
    }
    router.replace(`/node/${id}`);
  }, [router]);

  return (
    <div className="fixed inset-0 grid place-items-center bg-cream text-ink">
      <div className="flex flex-col items-center gap-4">
        <LogoMark size={48} />
        <div className="text-[17px] font-semibold">Installing your DigitalHeat server…</div>
      </div>
    </div>
  );
}
