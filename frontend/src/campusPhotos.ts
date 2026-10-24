// Photo slots for the Home page. Until real photos are added, hero and gallery slots show
// original illustrated Collegiate Gothic scenes (GothicScene.tsx) and reel slots show an activity icon.
// Drop a .jpg with the matching name into frontend/public/campus/
// and it appears automatically; until then a refined placeholder panel is shown.
// See public/campus/README.md for the checklist, sizes and licensing notes.

export type Tone = "dusk" | "autumn" | "stone" | "snow" | "green" | "night" | "river";

export type SceneKind = "tower" | "cloister" | "gate" | "library" | "quad";
export type Activity = "crew" | "study" | "frisbee" | "game" | "music" | "hockey" | "lab" | "art" | "friends" | "grad";

export type Photo = {
  scene?: SceneKind;   // illustrated Gothic fallback while the photo is missing
  activity?: Activity; // icon shown on reel placeholders
  file: string;      // name inside public/campus/
  alt: string;       // describes the photo for screen readers
  caption: string;   // shown on the page
  place: string;     // small label above the caption
  tone: Tone;        // placeholder color while the photo is missing
};

const src = (file: string) => `/campus/${file}`;
export const photoUrl = (p: Photo) => src(p.file);

// Hero slideshow (cross-fades). Landscape, at least 2400×1400.
export const HERO_SLIDES: Photo[] = [
  { scene: "tower", file: "hero-harkness-dusk.jpg", place: "Harkness Tower", caption: "Evening light over the Gothic spires", alt: "Harkness Tower at dusk", tone: "dusk" },
  { scene: "quad", file: "hero-old-campus-autumn.jpg", place: "Old Campus", caption: "Elms turning gold in October", alt: "Old Campus lawn in autumn", tone: "autumn" },
  { scene: "library", file: "hero-sterling-library.jpg", place: "Sterling Memorial Library", caption: "The cathedral of learning", alt: "Sterling Memorial Library interior nave", tone: "stone" },
  { scene: "quad", file: "hero-beinecke-snow.jpg", place: "Beinecke Library", caption: "Winter quiet on Hewitt Quadrangle", alt: "Beinecke Rare Book Library in snow", tone: "snow" },
];

// "The beauty of campus" gallery. Mixed orientation, at least 1600 px on the long side.
export const CAMPUS_SCENES: Photo[] = [
  { scene: "quad", file: "scene-cross-campus.jpg", place: "Cross Campus", caption: "Spring afternoon on the lawn", alt: "Students relaxing on Cross Campus lawn", tone: "green" },
  { scene: "cloister", file: "scene-college-courtyard.jpg", place: "Residential college", caption: "Ivy and stone courtyards", alt: "A residential college courtyard with ivy", tone: "stone" },
  { scene: "gate", file: "scene-phelps-gate.jpg", place: "Phelps Gate", caption: "The gateway to Old Campus", alt: "Phelps Gate archway", tone: "dusk" },
  { scene: "cloister", file: "scene-yale-bowl.jpg", place: "Yale Bowl", caption: "Game day in the Bowl", alt: "The Yale Bowl stadium on game day", tone: "autumn" },
  { scene: "tower", file: "scene-snow-old-campus.jpg", place: "Old Campus", caption: "First snow of the semester", alt: "Old Campus covered in snow", tone: "snow" },
];

// Moving reel of student life. Portrait 4:5, at least 1000×1250.
export const STUDENT_REEL: Photo[] = [
  { activity: "crew", file: "reel-crew.jpg", place: "Housatonic River", caption: "Crew practice at sunrise", alt: "Rowers on the river at sunrise", tone: "river" },
  { activity: "study", file: "reel-library-study.jpg", place: "Sterling Library", caption: "Late-night study session", alt: "Students studying in a library reading room", tone: "stone" },
  { activity: "frisbee", file: "reel-frisbee.jpg", place: "Old Campus", caption: "Frisbee between classes", alt: "Students playing frisbee on a lawn", tone: "green" },
  { activity: "game", file: "reel-the-game.jpg", place: "Yale Bowl", caption: "Cheering at The Game", alt: "Students cheering in the stands", tone: "autumn" },
  { activity: "music", file: "reel-a-cappella.jpg", place: "Battell Chapel", caption: "A cappella rehearsal", alt: "Student singers rehearsing", tone: "dusk" },
  { activity: "hockey", file: "reel-hockey.jpg", place: "Ingalls Rink", caption: "Friday night hockey", alt: "Students at an ice hockey game", tone: "night" },
  { activity: "lab", file: "reel-lab.jpg", place: "Science Hill", caption: "Research in the lab", alt: "Students working in a research lab", tone: "stone" },
  { activity: "art", file: "reel-art-studio.jpg", place: "School of Art", caption: "Studio critique", alt: "Students in an art studio", tone: "autumn" },
  { activity: "friends", file: "reel-friends.jpg", place: "Cross Campus", caption: "Friends in Yale blue", alt: "Friends wearing Yale sweatshirts on campus", tone: "green" },
  { activity: "grad", file: "reel-commencement.jpg", place: "Old Campus", caption: "Commencement morning", alt: "Graduates at commencement", tone: "snow" },
];
