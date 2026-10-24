const YALE_TIMELINE = [
  { year: "1701", text: "Connecticut clergy charter the Collegiate School, the third-oldest institution of higher learning in the United States." },
  { year: "1716", text: "The school moves to New Haven. Two years later it is renamed Yale College in honor of benefactor Elihu Yale." },
  { year: "1875", text: "Yale meets Harvard on the football field for the first time. The Game becomes one of college sports' oldest rivalries." },
  { year: "1889", text: "Handsome Dan, a bulldog, becomes the first live college mascot in America. The Bulldogs have been Yale's ever since." },
  { year: "1921", text: "Harkness Tower is completed. Its carillon still rings out over the campus." },
  { year: "1933", text: "The residential college system opens, giving every student a home within the university." },
];

const VALUES = [
  { title: "Family First", text: "We are a family-run business, and every customer who walks in is treated like one of our own." },
  { title: "Quality That Lasts", text: "We choose apparel that holds up through four years of New Haven winters and many reunions after." },
  { title: "Pride in New Haven", text: "We have been part of the neighborhood since 1975, through every graduation, every Game and every Commencement." },
];

export default function About() {
  return (
    <>
      <section className="page-header">
        <div className="container">
          <p className="eyebrow">About Us</p>
          <h1 className="page-header__title">A Family Tradition Since 1975</h1>
          <p className="page-header__lede">
            Campus Customs has been outfitting the Yale community for more than half a century.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container split">
          <div>
            <h2 className="section__title">Our Story</h2>
            <p>
              Campus Customs opened in New Haven in 1975 with a simple idea: Yale students, alumni and
              fans deserve apparel that carries the name with the same pride they do. More than fifty
              years later, we are still a family-run shop and still focused on that idea.
            </p>
            <p>
              Generations of Bulldogs have come to us for their first Yale sweatshirt, a hoodie for
              the Harvard-Yale game, or a gift for a new graduate. Some of the families who shop with
              us today first came in as students decades ago.
            </p>
          </div>
          <aside className="crest" aria-hidden="true">
            <span className="crest__est">Est.</span>
            <span className="crest__year">1975</span>
            <span className="crest__motto">Lux et Veritas</span>
          </aside>
        </div>
      </section>

      <section className="section section--cream">
        <div className="container">
          <p className="eyebrow eyebrow--blue">The University We Celebrate</p>
          <h2 className="section__title">The Rich History of Yale</h2>
          <p className="section__intro">
            Every piece we sell carries more than three hundred years of history. The university's
            motto, <em>Lux et Veritas</em> ("Light and Truth"), and its signature Yale blue are known
            around the world.
          </p>
          <ol className="timeline">
            {YALE_TIMELINE.map((t) => (
              <li key={t.year} className="timeline__item">
                <span className="timeline__year">{t.year}</span>
                <p>{t.text}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2 className="section__title">What We Stand For</h2>
          <div className="grid grid--3">
            {VALUES.map((v) => (
              <article key={v.title} className="card">
                <h3 className="card__title">{v.title}</h3>
                <p>{v.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
