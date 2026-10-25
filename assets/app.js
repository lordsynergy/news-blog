const categories = [
  { id: "psychology", title: "Психология", note: "Разум, поведение и общество" },
  { id: "chemistry", title: "Химия", note: "Вещества, реакции и материалы" },
  { id: "biology", title: "Биология", note: "Жизнь, клетки и экосистемы" },
];

const dateFormatter = new Intl.DateTimeFormat("ru-RU", {
  day: "numeric",
  month: "long",
  year: "numeric",
});

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  })[character]);
}

function safeDate(value) {
  const date = new Date(`${value}T12:00:00Z`);
  return Number.isNaN(date.getTime()) ? value : dateFormatter.format(date);
}

function cardMarkup(item, index) {
  return `
    <article class="news-card">
      <div class="card-meta">
        <span>${String(index + 1).padStart(2, "0")}</span>
        <span>${escapeHtml(item.source)}</span>
      </div>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.summary)}</p>
      <a class="read-more" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">
        Читать источник <span aria-hidden="true">→</span>
      </a>
    </article>`;
}

function sectionMarkup(category, items, index) {
  return `
    <section class="news-section" id="${category.id}">
      <div class="section-heading">
        <span class="section-number">0${index + 1}</span>
        <h2>${category.title}</h2>
        <p class="section-kicker">${category.note}</p>
      </div>
      <div class="cards">${items.map(cardMarkup).join("")}</div>
    </section>`;
}

async function loadNews() {
  const root = document.querySelector("#news-root");
  try {
    const response = await fetch(`data/news.json?v=${Date.now()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    root.innerHTML = categories
      .map((category, index) => sectionMarkup(category, data.categories[category.id] || [], index))
      .join("");
    document.querySelector("#issue-label").textContent = `Выпуск от ${safeDate(data.updated_at)}`;
  } catch (error) {
    console.error("Не удалось загрузить выпуск", error);
    root.innerHTML = '<div class="error-state"><p>Не удалось загрузить выпуск.<br>Попробуйте обновить страницу немного позже.</p></div>';
    document.querySelector("#issue-label").textContent = "Выпуск временно недоступен";
  }
}

loadNews();
