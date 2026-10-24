import { useState } from "react";
import { photoUrl, type Activity, type Photo } from "../campusPhotos.ts";
import GothicScene from "./GothicScene.tsx";

// Simple line icons for student-life reel placeholders.
const ICONS: Record<Activity, string> = {
  crew: "M3 17c3 0 3-1.5 6-1.5S12 17 15 17s3-1.5 6-1.5M5 13l14-8M15 3l4 2-1 2",
  study: "M4 5h6a2 2 0 0 1 2 2v12a2 2 0 0 0-2-2H4zM20 5h-6a2 2 0 0 0-2 2v12a2 2 0 0 1 2-2h6z",
  frisbee: "M3 12c0-3 4-5 9-5s9 2 9 5-4 5-9 5-9-2-9-5zM7 12c1 1 3 1.5 5 1.5s4-.5 5-1.5",
  game: "M12 3v18M5 7h14M5 17h14M8 3l-3 4M16 3l3 4",
  music: "M9 18V6l10-2v12M9 18a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0zM19 16a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z",
  hockey: "M6 3l5 13c.4 1 1.3 2 3 2h5M4 20h6M17 20a2 1 0 1 0 4 0 2 1 0 1 0-4 0",
  lab: "M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3M7 15h10",
  art: "M12 3a9 9 0 1 0 0 18c1.5 0 2-1 2-2s-1-1.5-1-2.5 1-1.5 2-1.5h2a4 4 0 0 0 4-4c0-4.4-4-8-9-8zM7.5 11h.01M10 7h.01M15 7h.01",
  friends: "M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM16 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM2 20c0-3 3-5 6-5s6 2 6 5M12 17c1-1.3 2.4-2 4-2 3 0 6 2 6 5",
  grad: "M2 9l10-5 10 5-10 5zM6 11v5c3 2 9 2 12 0v-5M22 9v6",
};

// Shows the photo if public/campus/<file> exists; otherwise an elegant placeholder panel
// in the photo's tone. In development the panel also shows which file to add.
export default function PhotoSlot({
  photo, className = "", eager = false, showCaption = true,
}: { photo: Photo; className?: string; eager?: boolean; showCaption?: boolean }) {
  const [state, setState] = useState<"loading" | "ok" | "missing">("loading");

  return (
    <figure className={`photo photo--${photo.tone} photo--${state} ${className}`}>
      {state !== "missing" && (
        <img
          src={photoUrl(photo)}
          alt={photo.alt}
          loading={eager ? "eager" : "lazy"}
          onLoad={() => setState("ok")}
          onError={() => setState("missing")}
        />
      )}
      {state === "missing" && (
        <div className="photo__placeholder" aria-label={photo.alt} role="img">
          {photo.scene ? (
            <GothicScene kind={photo.scene} tone={photo.tone} />
          ) : (
            <>
              <svg className="photo__pattern" viewBox="0 0 120 120" aria-hidden="true">
                <defs>
                  <pattern id={`arch-${photo.file}`} width="40" height="60" patternUnits="userSpaceOnUse">
                    <path d="M4 60 V26 Q4 6 20 2 Q36 6 36 26 V60" fill="none" stroke="currentColor" strokeWidth=".8" />
                    <path d="M12 60 V30 Q12 16 20 13 Q28 16 28 30 V60" fill="none" stroke="currentColor" strokeWidth=".5" />
                  </pattern>
                </defs>
                <rect width="120" height="120" fill={`url(#arch-${photo.file})`} />
              </svg>
              {photo.activity && (
                <svg className="photo__icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path d={ICONS[photo.activity]} fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </>
          )}
          {import.meta.env.DEV && <span className="photo__todo">Add photo: campus/{photo.file}</span>}
        </div>
      )}
      {showCaption && (
        <figcaption className="photo__caption">
          <span className="photo__place">{photo.place}</span>
          <span className="photo__text">{photo.caption}</span>
        </figcaption>
      )}
    </figure>
  );
}
