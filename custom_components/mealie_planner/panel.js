const ICONS = {
  calendar: "M19 19H5V8h14m-3-7v2H8V1H6v2H5c-1.11 0-2 .89-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2h-1V1m-1 11h-5v5h5v-5Z",
  basket: "M5.5 21c-.78 0-1.46-.45-1.79-1.1L1.1 11.4 1 11a1 1 0 0 1 1-1h4.58l4.6-6.57a.997.997 0 0 1 1.65-.01L17.42 10H22a1 1 0 0 1 1 1l-.04.29-2.67 8.61c-.33.65-1.01 1.1-1.79 1.1h-13M12 5.74 9 10h6l-3-4.26M12 13a2 2 0 0 0-2 2 2 2 0 0 0 2 2 2 2 0 0 0 2-2 2 2 0 0 0-2-2Z",
  tag: "M5.5 7A1.5 1.5 0 0 1 4 5.5 1.5 1.5 0 0 1 5.5 4 1.5 1.5 0 0 1 7 5.5 1.5 1.5 0 0 1 5.5 7m15.91 4.58-9-9C12.05 2.22 11.55 2 11 2H4c-1.11 0-2 .89-2 2v7c0 .55.22 1.05.59 1.41l8.99 9c.37.36.87.59 1.42.59.55 0 1.05-.23 1.41-.59l7-7c.37-.36.59-.86.59-1.41 0-.56-.23-1.06-.59-1.42Z",
  cog: "M12 15.5A3.5 3.5 0 0 1 8.5 12 3.5 3.5 0 0 1 12 8.5a3.5 3.5 0 0 1 3.5 3.5 3.5 3.5 0 0 1-3.5 3.5m7.43-2.53c.04-.32.07-.64.07-.97 0-.33-.03-.66-.07-1l2.11-1.63c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.31-.61-.22l-2.49 1c-.52-.39-1.06-.73-1.69-.98l-.37-2.65A.506.506 0 0 0 14 2h-4c-.25 0-.46.18-.5.42l-.37 2.65c-.63.25-1.17.59-1.69.98l-2.49-1c-.22-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64L4.57 11c-.04.34-.07.67-.07 1 0 .33.03.65.07.97l-2.11 1.66c-.19.15-.25.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1.01c.52.4 1.06.74 1.69.99l.37 2.65c.04.24.25.42.5.42h4c.25 0 .46-.18.5-.42l.37-2.65c.63-.26 1.17-.59 1.69-.99l2.49 1.01c.22.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.66Z",
  left: "M15.41 16.58 10.83 12l4.58-4.59L14 6l-6 6 6 6 1.41-1.42Z",
  right: "M8.59 16.58 13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.42Z",
  magic: "M7.5 5.6 5 7l1.4-2.5L5 2l2.5 1.4L10 2 8.6 4.5 10 7 7.5 5.6m12 9.8L22 14l-1.4 2.5L22 19l-2.5-1.4L17 19l1.4-2.5L17 14l2.5 1.4M22 2l-1.4 2.5L22 7l-2.5-1.4L17 7l1.4-2.5L17 2l2.5 1.4L22 2m-8.66 10.78 2.44-2.44-2.12-2.12-2.44 2.44 2.12 2.12m1.03-5.49 2.34 2.34c.39.37.39 1.02 0 1.41L5.04 22.71c-.39.39-1.04.39-1.41 0l-2.34-2.34c-.39-.37-.39-1.02 0-1.41L12.96 7.29c.39-.39 1.04-.39 1.41 0Z",
  save: "M15 9H5V5h10m-3 14a3 3 0 0 1-3-3 3 3 0 0 1 3-3 3 3 0 0 1 3 3 3 3 0 0 1-3 3m5-16H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7l-4-4Z",
  lock: "M12 17a2 2 0 0 0 2-2 2 2 0 0 0-2-2 2 2 0 0 0-2 2 2 2 0 0 0 2 2m6-9a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2h1V6a5 5 0 0 1 5-5 5 5 0 0 1 5 5v2h1m-6-5a3 3 0 0 0-3 3v2h6V6a3 3 0 0 0-3-3Z",
  unlock: "M18 8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2h9V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3H7a5 5 0 0 1 5-5 5 5 0 0 1 5 5v2h1m-6 9a2 2 0 0 0 2-2 2 2 0 0 0-2-2 2 2 0 0 0-2 2 2 2 0 0 0 2 2Z",
  swap: "M21 9 17 5v3h-7v2h7v3m-10-2-4 4 4 4v-3h7v-2H7v-3l-4 4Z",
  close: "M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41Z",
  edit: "M20.71 7.04c.39-.39.39-1.04 0-1.41l-2.34-2.34c-.37-.39-1.02-.39-1.41 0l-1.84 1.83 3.75 3.75M3 17.25V21h3.75L17.81 9.93l-3.75-3.75L3 17.25Z",
  plus: "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2Z",
  check: "M21 7 9 19l-5.5-5.5 1.41-1.41L9 16.17 19.59 5.59 21 7Z",
  refresh: "M17.65 6.35A7.958 7.958 0 0 0 12 4a8 8 0 0 0-8 8 8 8 0 0 0 8 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0 1 12 18a6 6 0 0 1-6-6 6 6 0 0 1 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35Z",
  open: "M14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7m5 16H5V5h7V3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7h-2v7Z",
  up: "M7.41 15.41 12 10.83l4.59 4.58L18 14l-6-6-6 6 1.41 1.41Z",
  down: "M7.41 8.58 12 13.17l4.59-4.59L18 10l-6 6-6-6 1.41-1.42Z",
  delete: "M19 4h-3.5l-1-1h-5l-1 1H5v2h14M6 19a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7H6v12Z",
  search: "M9.5 3A6.5 6.5 0 0 1 16 9.5c0 1.61-.59 3.09-1.56 4.23l.27.27h.79l5 5-1.5 1.5-5-5v-.79l-.27-.27A6.52 6.52 0 0 1 9.5 16 6.5 6.5 0 0 1 3 9.5 6.5 6.5 0 0 1 9.5 3m0 2C7 5 5 7 5 9.5S7 14 9.5 14 14 12 14 9.5 12 5 9.5 5Z",
};

const CHAINS = { lidl: "Lidl", kaufland: "Kaufland", billa: "Billa" };
const CHAIN_COLORS = { lidl: "#0050aa", kaufland: "#e10915", billa: "#ffd200" };
const MEALS = ["breakfast", "lunch", "dinner", "side", "snack", "dessert", "drink"];
const CATEGORIES = ["fish", "meat", "vegetables", "fruit", "dairy", "legumes", "bakery", "pantry", "frozen", "drinks", "other_food", "non_food"];

const TEXT = {
  bg: {
    plan: "План", products: "Продукти", offers: "Промоции", settings: "Настройки",
    week: "Седмица", generate: "Състави седмицата", again: "Друг вариант", save: "Запази в Mealie",
    replaceSaved: "Замени и записаното в Mealie", local: "Локално", ai: "AI",
    saved: "Записано", changed: "Променено", add: "Добави", change: "Смени", clear: "Махни",
    lock: "Заключи", unlock: "Отключи", move: "Размени", moveHint: "Избери хранене, с което да размениш.",
    empty: "Празно", pickTitle: "Рецепта за {slot}", search: "Търси рецепта…", needed: "нужна за правилата",
    onSale: "{n} в промоция", noRecipes: "Няма рецепти.", open: "Отвори в Mealie",
    rulesTitle: "Правила", notice_ai_failed: "AI не успя; седмицата е съставена локално.",
    savedMsg: "Записани {written}, премахнати {removed} в Mealie.", nothingPlanned: "Седмицата още е празна. Натисни „Състави седмицата“.",
    state_ok: "изпълнено", state_missing: "не е изпълнено", state_short: "по възможност", state_over: "над максимума",
    basketEmpty: "Планът още няма рецепти, затова няма и продукти.", noShop: "Без магазин",
    selectSale: "Избери всички в промоция", selectNone: "Изчисти избора", addToList: "Добави в списъка ({n})",
    added: "Добавени {n} в списъка.", listMissing: "Инсталирай HomeBasket Lists, за да добавяш в списък.",
    listPick: "Списък", homeShop: "Не е в промоция; купува се тук според HomeBasket Lists", recipesFor: "за", byHand: "избрано ръчно", matches: "{n} подходящи",
    similar: "Подобни продукти", sim_food: "Същата храна", sim_name: "Подобно име", sim_category: "Същия вид",
    choose: "Избери", auto: "Автоматично", noOffer: "Не е в промоция", validity: "Валидно", noDates: "без дата", zoomPage: "Цялата страница", zoomProduct: "Само продукта", until: "до",
    unit_kg: "кг", unit_l: "л", unit_pc: "бр.", page: "стр.", unitPrice: "{price} €/{unit}", estimate: "Сума на избраните в промоция: {sum} €",
    refresh: "Провери за нови", refreshing: "Проверява…", rescan: "Прочети отново", addBrochure: "Добави брошура",
    probe: "Проверка на източниците", tokens: "AI: {p} + {c} токена", web: "Сайт", brochure: "Брошура",
    count: "{n} промоции", error: "Грешка", lastCheck: "Проверено", filterText: "Търси продукт…",
    all: "Всички", today: "Валидни днес", planWeek: "В планираната седмица", anyDate: "Всички дати",
    minDiscount: "Отстъпка", sortBy: "Подреди", sort_discount: "Най-голяма отстъпка", sort_price: "Най-ниска цена",
    sort_unit: "Най-ниска цена за кг/л", sort_name: "Име", sort_expiry: "Изтичат скоро", sort_chain: "Магазин",
    more: "Покажи още", noOffers: "Няма промоции по тези филтри.", shown: "{n} от {total}",
    url: "Адрес на PDF, изображение или страница", chain: "Магазин", title: "Заглавие", from: "От", to: "До", read: "Прочети",
    reading: "AI чете брошурата… може да отнеме минути.", rules: "Правила", required: "Задължително", preferred: "Пожелателно",
    min: "Мин.", max: "Макс.", contains: "Съдържа", excludes: "Не съдържа", tags: "Етикети", categories: "Категории",
    foods: "Храни (със запетая)", addRule: "Ново правило", presets: "Готови правила", meals: "Хранения по дни",
    recent: "Без повторение на рецепти от последните седмици", saveSettings: "Запази настройките", settingsSaved: "Настройките са запазени.",
    ruleName: "Име", moreOptions: "Магазините и зоните им, брошурите за AI, страниците от брошура, списъкът и AI се задават в опциите на интеграцията: Настройки → Устройства и услуги → Mealie Planner → зъбното колело.", openOptions: "Към интеграцията", adminOnly: "Настройките се променят от администратор.", close: "Затвори", status: "Източници",
    brochuresOff: "Четенето на брошури е изключено или няма AI.",
    days: ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"],
    daysLong: ["понеделник", "вторник", "сряда", "четвъртък", "петък", "събота", "неделя"],
    meal_breakfast: "Закуска", meal_lunch: "Обяд", meal_dinner: "Вечеря", meal_side: "Гарнитура", meal_snack: "Междинно", meal_dessert: "Десерт", meal_drink: "Напитка",
    cat_fish: "Риба", cat_meat: "Месо", cat_vegetables: "Зеленчуци", cat_fruit: "Плодове", cat_dairy: "Млечни и яйца",
    cat_legumes: "Бобови", cat_bakery: "Хляб и тестени", cat_pantry: "Бакалия", cat_frozen: "Замразени", cat_drinks: "Напитки",
    cat_other_food: "Други храни", cat_non_food: "Нехранителни",
  },
  en: {
    plan: "Plan", products: "Products", offers: "Offers", settings: "Settings",
    week: "Week", generate: "Plan the week", again: "Another option", save: "Save to Mealie",
    replaceSaved: "Also replace what is saved in Mealie", local: "Local", ai: "AI",
    saved: "Saved", changed: "Changed", add: "Add", change: "Change", clear: "Remove",
    lock: "Lock", unlock: "Unlock", move: "Swap", moveHint: "Choose the meal to swap with.",
    empty: "Empty", pickTitle: "Recipe for {slot}", search: "Search recipes…", needed: "needed for the rules",
    onSale: "{n} on sale", noRecipes: "No recipes.", open: "Open in Mealie",
    rulesTitle: "Rules", notice_ai_failed: "AI failed; the week was planned locally.",
    savedMsg: "{written} written, {removed} removed in Mealie.", nothingPlanned: "The week is empty. Press “Plan the week”.",
    state_ok: "met", state_missing: "not met", state_short: "if possible", state_over: "over the maximum",
    basketEmpty: "The plan has no recipes yet, so there are no products.", noShop: "No shop",
    selectSale: "Select all on sale", selectNone: "Clear selection", addToList: "Add to list ({n})",
    added: "{n} added to the list.", listMissing: "Install HomeBasket Lists to add to a list.",
    listPick: "List", homeShop: "Not on sale; bought here according to HomeBasket Lists", recipesFor: "for", byHand: "picked by hand", matches: "{n} matching",
    similar: "Similar products", sim_food: "Same food", sim_name: "Similar name", sim_category: "Same kind",
    choose: "Choose", auto: "Automatic", noOffer: "Not on sale", validity: "Valid", noDates: "no dates", zoomPage: "Whole page", zoomProduct: "Just the product", until: "until",
    unit_kg: "kg", unit_l: "l", unit_pc: "pc", page: "p.", unitPrice: "{price} €/{unit}", estimate: "Selected items on sale: {sum} €",
    refresh: "Check for new", refreshing: "Checking…", rescan: "Read again", addBrochure: "Add brochure",
    probe: "Check the sources", tokens: "AI: {p} + {c} tokens", web: "Website", brochure: "Brochure",
    count: "{n} offers", error: "Error", lastCheck: "Checked", filterText: "Search products…",
    all: "All", today: "Valid today", planWeek: "In the planned week", anyDate: "Any date",
    minDiscount: "Discount", sortBy: "Sort", sort_discount: "Biggest discount", sort_price: "Lowest price",
    sort_unit: "Lowest price per kg/l", sort_name: "Name", sort_expiry: "Ending soon", sort_chain: "Shop",
    more: "Show more", noOffers: "No offers match these filters.", shown: "{n} of {total}",
    url: "URL of a PDF, image or page", chain: "Shop", title: "Title", from: "From", to: "To", read: "Read",
    reading: "AI is reading the brochure… this can take minutes.", rules: "Rules", required: "Required", preferred: "Preferred",
    min: "Min", max: "Max", contains: "Contains", excludes: "Does not contain", tags: "Tags", categories: "Categories",
    foods: "Foods (comma separated)", addRule: "New rule", presets: "Ready-made rules", meals: "Meals per day",
    recent: "Don't repeat recipes from the last weeks", saveSettings: "Save settings", settingsSaved: "Settings saved.",
    ruleName: "Name", moreOptions: "Shops and their zones, which brochures AI reads, brochure pages, the list and AI are set in the integration options: Settings → Devices & services → Mealie Planner → the gear.", openOptions: "Open the integration", adminOnly: "Only an administrator can change the settings.", close: "Close", status: "Sources",
    brochuresOff: "Brochure reading is off, or there is no AI.",
    days: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    daysLong: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    meal_breakfast: "Breakfast", meal_lunch: "Lunch", meal_dinner: "Dinner", meal_side: "Side", meal_snack: "Snack", meal_dessert: "Dessert", meal_drink: "Drink",
    cat_fish: "Fish", cat_meat: "Meat", cat_vegetables: "Vegetables", cat_fruit: "Fruit", cat_dairy: "Dairy & eggs",
    cat_legumes: "Legumes", cat_bakery: "Bakery", cat_pantry: "Pantry", cat_frozen: "Frozen", cat_drinks: "Drinks",
    cat_other_food: "Other food", cat_non_food: "Non-food",
  },
};

function icon(name, size = 18) {
  return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" aria-hidden="true"><path fill="currentColor" d="${ICONS[name]}"/></svg>`;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function storage(key, value) {
  try {
    if (value === undefined) return localStorage.getItem(key);
    localStorage.setItem(key, value);
  } catch (error) { /* storage unavailable */ }
  return null;
}

function money(value) {
  return value == null ? "" : Number(value).toFixed(2).replace(".", ",");
}

function parseDate(iso) {
  const [y, m, d] = String(iso).split("-").map(Number);
  return new Date(y, m - 1, d);
}

function short(iso) {
  if (!iso) return "";
  const d = parseDate(iso);
  return `${String(d.getDate()).padStart(2, "0")}.${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function addDays(iso, days) {
  const d = parseDate(iso);
  d.setDate(d.getDate() + days);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function todayIso() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function weekday(iso) {
  return (parseDate(iso).getDay() + 6) % 7;
}

class MealiePlannerPanel extends HTMLElement {
  set hass(value) {
    const first = !this._hass;
    this._hass = value;
    if (this._menu) this._menu.hass = value;
    if (first) this._mount();
  }

  set narrow(value) {
    this._narrow = value;
    if (this._menu) this._menu.narrow = value;
  }

  disconnectedCallback() {
    clearTimeout(this._poll);
  }

  t(key, vars = {}) {
    const table = TEXT[this._lang] || TEXT.en;
    let text = table[key] ?? TEXT.en[key] ?? key;
    for (const [name, value] of Object.entries(vars)) text = text.replace(`{${name}}`, value);
    return text;
  }

  async _mount() {
    this._lang = String(this._hass.language || "en").startsWith("bg") ? "bg" : "en";
    this._tab = storage("mealie-planner-tab") || "plan";
    this._filters = { text: "", chains: [], categories: [], date: "week", discount: 0, sort: "discount", limit: 60 };
    try { Object.assign(this._filters, JSON.parse(storage("mealie-planner-filters") || "{}"), { text: "", limit: 60 }); } catch (error) { /* ignore */ }
    this._moving = null;
    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        :host {
          --mp-accent: var(--primary-color, #03a9f4);
          --mp-card: var(--card-background-color, #fff);
          --mp-surface: var(--secondary-background-color, #f3f3f3);
          --mp-text: var(--primary-text-color, #212121);
          --mp-muted: var(--secondary-text-color, #727272);
          --mp-line: var(--divider-color, rgba(0,0,0,.12));
          --mp-success: var(--success-color, #43a047);
          --mp-warning: var(--warning-color, #ffa600);
          --mp-error: var(--error-color, #db4437);
          display:block; min-height:100%; color:var(--mp-text); background:var(--primary-background-color);
          font-family:var(--ha-font-family-body, Roboto, system-ui, sans-serif); -webkit-tap-highlight-color:transparent;
        }
        * { box-sizing:border-box }
        [hidden] { display:none !important }
        button, select, input, textarea { font:inherit; color:inherit }
        button { cursor:pointer; border:0; background:none }
        button:disabled { opacity:.5; cursor:default }
        svg { flex:none; display:block }
        a { color:inherit }
        .toolbar { display:flex; align-items:center; height:var(--header-height, 56px); padding:0 12px; gap:8px;
          background:var(--app-header-background-color, var(--mp-accent)); color:var(--app-header-text-color, #fff);
          border-bottom:var(--app-header-border-bottom, none); font-size:20px }
        .tabs { display:flex; gap:4px; padding:8px 16px 0; max-width:1180px; margin:0 auto; overflow-x:auto }
        .tab { display:flex; align-items:center; gap:6px; padding:10px 16px; border-radius:20px; color:var(--mp-muted); white-space:nowrap; font-weight:500 }
        .tab[aria-selected="true"] { background:color-mix(in srgb, var(--mp-accent) 16%, transparent); color:var(--mp-accent) }
        main { max-width:1180px; margin:0 auto; padding:16px 16px 96px }
        .bar { display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin-bottom:14px }
        .grow { flex:1 }
        .weeknav { display:flex; align-items:center; gap:4px; background:var(--mp-card); border:1px solid var(--mp-line); border-radius:22px; padding:3px }
        .weeknav span { padding:0 8px; font-weight:500; font-variant-numeric:tabular-nums }
        .round { display:grid; place-items:center; width:36px; height:36px; border-radius:50% }
        .round:hover { background:var(--mp-surface) }
        .btn { display:inline-flex; align-items:center; gap:6px; padding:9px 16px; border-radius:20px; background:var(--mp-surface); font-weight:500 }
        .btn.primary { background:var(--mp-accent); color:var(--text-primary-color, #fff) }
        .btn.small { padding:6px 12px; font-size:13px }
        .chip { display:inline-flex; align-items:center; gap:4px; padding:6px 12px; border-radius:16px; font-size:13px; background:var(--mp-surface); border:1px solid transparent }
        .chip[aria-pressed="true"] { background:color-mix(in srgb, var(--mp-accent) 18%, transparent); color:var(--mp-accent); border-color:color-mix(in srgb, var(--mp-accent) 45%, transparent); font-weight:500 }
        label.check { display:inline-flex; align-items:center; gap:6px; font-size:14px; color:var(--mp-muted) }
        .rules { display:flex; flex-wrap:wrap; gap:6px; margin:0 0 14px }
        .rule { font-size:13px; padding:5px 10px; border-radius:14px; background:var(--mp-surface) }
        .rule.ok { background:color-mix(in srgb, var(--mp-success) 16%, transparent) }
        .rule.missing, .rule.over { background:color-mix(in srgb, var(--mp-error) 16%, transparent) }
        .rule.short { background:color-mix(in srgb, var(--mp-warning) 20%, transparent) }
        .notice { padding:10px 14px; border-radius:12px; background:color-mix(in srgb, var(--mp-warning) 18%, transparent); margin-bottom:12px; font-size:14px }
        .week { display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:14px }
        .day { background:var(--mp-card); border:1px solid var(--mp-line); border-radius:18px; padding:12px; display:flex; flex-direction:column; gap:10px }
        .day h3 { margin:0; font-size:15px; display:flex; justify-content:space-between; color:var(--mp-muted); font-weight:500 }
        .day h3 b { color:var(--mp-text) }
        .slot { position:relative; border-radius:14px; background:var(--mp-surface); padding:10px; display:flex; gap:10px }
        .slot.moving { outline:2px dashed var(--mp-accent) }
        .slot.target { cursor:pointer; outline:2px solid color-mix(in srgb, var(--mp-accent) 40%, transparent) }
        .thumb { width:56px; height:56px; border-radius:10px; object-fit:cover; background:var(--mp-line); flex:none }
        .slot .body { flex:1; min-width:0; display:flex; flex-direction:column; gap:4px }
        .meal { font-size:12px; color:var(--mp-muted); text-transform:uppercase; letter-spacing:.04em; display:flex; gap:6px; align-items:center }
        .meal .state { margin-left:auto; text-transform:none; letter-spacing:0 }
        .state.saved { color:var(--mp-success) }
        .state.changed { color:var(--mp-warning) }
        .name { font-weight:600; font-size:15px; line-height:1.3; text-decoration:none; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden }
        .badges { display:flex; flex-wrap:wrap; gap:4px }
        .badge { font-size:11.5px; padding:2px 8px; border-radius:10px; background:var(--mp-card); border:1px solid var(--mp-line) }
        .badge.sale { background:color-mix(in srgb, var(--mp-success) 18%, transparent); border-color:transparent }
        .badge.need { background:color-mix(in srgb, var(--mp-accent) 18%, transparent); border-color:transparent }
        .reason { font-size:12px; color:var(--mp-muted); font-style:italic }
        .tools { display:flex; gap:2px; margin-top:2px }
        .tools button { display:grid; place-items:center; width:32px; height:32px; border-radius:50%; color:var(--mp-muted) }
        .tools button:hover { background:var(--mp-card); color:var(--mp-text) }
        .tools button.on { color:var(--mp-accent) }
        .emptyslot { flex:1; display:flex; align-items:center; justify-content:space-between; color:var(--mp-muted) }
        .empty { text-align:center; padding:40px 16px; color:var(--mp-muted) }
        .group { background:var(--mp-card); border:1px solid var(--mp-line); border-radius:18px; margin-bottom:14px; overflow:hidden }
        .group > h3 { margin:0; padding:12px 16px; font-size:15px; display:flex; align-items:center; gap:8px; border-bottom:1px solid var(--mp-line) }
        .dot { width:12px; height:12px; border-radius:50%; background:var(--mp-muted) }
        .item { display:flex; align-items:center; gap:12px; padding:10px 16px; border-bottom:1px solid var(--mp-line); cursor:pointer }
        .item:last-child { border-bottom:0 }
        .item:hover { background:var(--mp-surface) }
        .item input { width:20px; height:20px; accent-color:var(--mp-accent); flex:none }
        .item .main { flex:1; min-width:0 }
        .item .title { font-weight:500 }
        .item .sub { font-size:12.5px; color:var(--mp-muted); overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
        .price { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap }
        .price b { font-size:16px }
        .price s { color:var(--mp-muted); font-size:12px; margin-left:4px }
        .price .off { display:inline-block; margin-left:4px; font-size:12px; color:#fff; background:var(--mp-error); border-radius:8px; padding:1px 6px }
        .price .dates { display:block; font-size:11.5px; color:var(--mp-muted) }
        .grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:14px }
        .offer { position:relative; background:var(--mp-card); border:1px solid var(--mp-line); border-radius:16px; overflow:hidden; display:flex; flex-direction:column }
        .offer .img { aspect-ratio:4/3; background:#fff; display:grid; place-items:center; overflow:hidden }
        .offer .img img { max-width:100%; max-height:100%; object-fit:contain }
        .offer .img .ph { font-size:38px; opacity:.5 }
        .offer .shop { position:absolute; top:8px; left:8px; font-size:12px; font-weight:700; padding:3px 9px; border-radius:10px; color:#fff }
        .offer .shop.billa { color:#222 }
        .offer .disc { position:absolute; top:8px; right:8px; font-size:13px; font-weight:700; padding:3px 8px; border-radius:10px; background:var(--mp-error); color:#fff }
        .offer .info { padding:10px 12px 12px; display:flex; flex-direction:column; gap:4px; flex:1 }
        .offer .oname { font-weight:500; line-height:1.3 }
        .offer .meta { font-size:12.5px; color:var(--mp-muted) }
        .offer .row { display:flex; align-items:baseline; gap:6px; margin-top:auto; padding-top:6px }
        .offer .row b { font-size:18px }
        .offer .row s { color:var(--mp-muted); font-size:13px }
        .offer .row button { margin-left:auto }
        .filters { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:12px }
        .filters input[type=search], select, .field input, .field textarea { background:var(--mp-card); border:1px solid var(--mp-line); border-radius:12px; padding:8px 12px }
        .filters input[type=search] { flex:1; min-width:180px }
        .sources { display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:10px; margin-bottom:14px }
        .source { background:var(--mp-card); border:1px solid var(--mp-line); border-radius:14px; padding:10px 12px; font-size:13px; display:flex; flex-direction:column; gap:4px }
        .source h4 { margin:0; display:flex; align-items:center; gap:6px; font-size:14px }
        .source .err { color:var(--mp-error) }
        .source .line { display:flex; gap:6px; align-items:center; justify-content:space-between }
        .muted { color:var(--mp-muted); font-size:13px }
        .card { background:var(--mp-card); border:1px solid var(--mp-line); border-radius:18px; padding:14px 16px; margin-bottom:14px }
        .card h3 { margin:0 0 10px; font-size:16px }
        .ruleedit { display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:8px; padding:12px; border-radius:14px; background:var(--mp-surface); margin-bottom:10px }
        .ruleedit .wide { grid-column:1 / -1 }
        .ruleedit .actions { grid-column:1 / -1; display:flex; justify-content:flex-end; gap:4px }
        .field { display:flex; flex-direction:column; gap:4px; font-size:12.5px; color:var(--mp-muted) }
        .field input, .field select, .field textarea { color:var(--mp-text); font-size:14px }
        .days { display:grid; grid-template-columns:auto repeat(${MEALS.length}, auto); gap:6px 12px; align-items:center; overflow-x:auto; font-size:13px }
        .days input { width:18px; height:18px; accent-color:var(--mp-accent) }
        dialog { border:0; border-radius:20px; padding:0; width:min(640px, calc(100% - 24px)); max-height:calc(100% - 48px); background:var(--mp-card); color:var(--mp-text); box-shadow:0 20px 60px rgba(0,0,0,.35) }
        dialog::backdrop { background:rgba(0,0,0,.4) }
        .zoomable { cursor:zoom-in }
        dialog.zoom { width:fit-content; max-width:calc(100vw - 24px); max-height:calc(100vh - 24px); background:#fff; color:#212121; padding:0; overflow:hidden }
        dialog.zoom::backdrop { background:rgba(0,0,0,.75) }
        .zoom .zbar { display:flex; align-items:center; gap:8px; padding:8px 8px 8px 16px; background:var(--mp-card); color:var(--mp-text) }
        .zoom .zbar b { flex:1; font-size:14px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap }
        .zoom img { display:block; height:min(calc(100vh - 80px), 1000px); width:auto; max-width:calc(100vw - 24px); margin:auto; object-fit:contain; cursor:zoom-out }
        .dhead { display:flex; align-items:center; gap:8px; padding:14px 16px; border-bottom:1px solid var(--mp-line); position:sticky; top:0; background:var(--mp-card); z-index:1 }
        .dhead h2 { margin:0; font-size:17px; flex:1 }
        .dbody { padding:12px 16px 16px; display:flex; flex-direction:column; gap:10px }
        .pick { display:flex; gap:10px; align-items:center; padding:8px; border-radius:12px; cursor:pointer; text-align:left; width:100% }
        .pick:hover { background:var(--mp-surface) }
        .pick .thumb { width:44px; height:44px }
        .pick .main { flex:1; min-width:0 }
        .current { display:flex; gap:12px; padding:12px; border-radius:14px; background:var(--mp-surface) }
        .current img { width:88px; height:88px; object-fit:contain; background:#fff; border-radius:10px }
        .alt { display:flex; align-items:center; gap:10px; padding:8px 4px; border-bottom:1px solid var(--mp-line) }
        .alt img { width:44px; height:44px; object-fit:contain; background:#fff; border-radius:8px }
        .alt .main { flex:1; min-width:0 }
        .simhead { font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:var(--mp-muted); margin-top:8px }
        pre { white-space:pre-wrap; font-size:12px; background:var(--mp-surface); padding:10px; border-radius:10px; margin:0; max-height:60vh; overflow:auto }
        .spinner { width:16px; height:16px; border-radius:50%; border:2px solid currentColor; border-right-color:transparent; animation:spin .8s linear infinite }
        @keyframes spin { to { transform:rotate(360deg) } }
        .toast { position:fixed; left:50%; bottom:24px; transform:translate(-50%, 20px); max-width:min(560px, calc(100% - 32px)); padding:12px 18px;
          border-radius:14px; background:var(--mp-text); color:var(--primary-background-color, #fff); font-size:14px; opacity:0; pointer-events:none; transition:opacity .25s, transform .25s; z-index:20 }
        .toast.show { opacity:1; transform:translate(-50%, 0) }
        @media (max-width:600px) {
          main { padding:12px 12px 96px }
          .week { grid-template-columns:1fr }
          .grid { grid-template-columns:repeat(2, minmax(0, 1fr)); gap:10px }
          .tab span { display:none }
        }
      </style>
      <div class="toolbar"><ha-menu-button></ha-menu-button><div>Mealie Planner</div></div>
      <nav class="tabs" role="tablist"></nav>
      <main id="main"></main>
      <dialog id="dialog"></dialog>
      <dialog id="zoom" class="zoom"></dialog>
      <div class="toast" id="toast" role="status"></div>
    `;
    this._menu = root.querySelector("ha-menu-button");
    this._menu.hass = this._hass;
    this._menu.narrow = this._narrow;
    this._main = root.getElementById("main");
    this._dialog = root.getElementById("dialog");
    this._zoom = root.getElementById("zoom");
    // A tap outside the picture closes it.
    this._zoom.addEventListener("click", (event) => { if (event.target === this._zoom) this._zoom.close(); });
    root.addEventListener("click", (event) => this._click(event));
    root.addEventListener("change", (event) => this._change(event));
    root.addEventListener("input", (event) => this._input(event));
    this._renderTabs();
    this._main.innerHTML = `<div class="empty"><div class="spinner" style="margin:auto"></div></div>`;
    try {
      this._state = await this._ws("state");
      this._week = this._state.week;
      await this._load();
    } catch (error) {
      this._main.innerHTML = `<div class="empty">${esc(error.message || error)}</div>`;
    }
  }

  _ws(command, data = {}) {
    return this._hass.callWS({ type: `mealie_planner/${command}`, ...data });
  }

  _toast(text) {
    const toast = this.shadowRoot.getElementById("toast");
    toast.textContent = text;
    toast.classList.add("show");
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => toast.classList.remove("show"), 4000);
  }

  async _run(button, action) {
    const old = button ? button.innerHTML : null;
    if (button) { button.disabled = true; button.innerHTML = `<span class="spinner"></span>`; }
    try {
      return await action();
    } catch (error) {
      this._toast(error.message || String(error));
      return null;
    } finally {
      if (button && button.isConnected) { button.disabled = false; button.innerHTML = old; }
    }
  }

  _renderTabs() {
    const tabs = [["plan", "calendar"], ["products", "basket"], ["offers", "tag"], ["settings", "cog"]];
    this.shadowRoot.querySelector(".tabs").innerHTML = tabs.map(([key, name]) =>
      `<button class="tab" role="tab" data-action="tab" data-tab="${key}" aria-selected="${this._tab === key}">${icon(name)}<span>${this.t(key)}</span></button>`).join("");
  }

  async _load() {
    if (this._tab === "offers") {
      this._offers = await this._ws("offers");
      this._render();
      this._watch();
      return;
    }
    if (this._tab === "settings") {
      this._settings = JSON.parse(JSON.stringify(await this._ws("settings/get")));
      this._render();
      if (!this._organizers) {
        this._ws("mealie/organizers").then((data) => { this._organizers = data; if (this._tab === "settings") this._render(); }).catch(() => {});
      }
      return;
    }
    this._view = await this._ws("plan/get", { week: this._week });
    if (!this._offers) this._ws("offers").then((data) => { this._offers = data; }).catch(() => {});
    this._render();
  }

  _watch() {
    clearTimeout(this._poll);
    if (this._offers && this._offers.refreshing) {
      this._poll = setTimeout(async () => {
        try { this._offers = await this._ws("offers"); } catch (error) { return; }
        if (this._tab === "offers") this._render();
        this._watch();
      }, 5000);
    }
  }

  _render() {
    if (this._tab === "plan") this._main.innerHTML = this._planHtml();
    else if (this._tab === "products") this._main.innerHTML = this._productsHtml();
    else if (this._tab === "offers") this._main.innerHTML = this._offersHtml();
    else this._main.innerHTML = this._settingsHtml();
  }

  // --- Plan -----------------------------------------------------------------
  _weekNav() {
    const view = this._view;
    const label = view ? `${short(view.week)} – ${short(view.end)}` : "";
    return `<div class="weeknav"><button class="round" data-action="week" data-step="-7" aria-label="←">${icon("left")}</button>
      <span>${esc(label)}</span><button class="round" data-action="week" data-step="7" aria-label="→">${icon("right")}</button></div>`;
  }

  _recipeUrl(recipe) {
    if (!recipe || !recipe.slug || !this._view) return null;
    return `${this._view.mealie_url}/g/${encodeURIComponent(this._view.group)}/r/${encodeURIComponent(recipe.slug)}`;
  }

  _thumb(recipe) {
    if (!recipe || !recipe.image || !this._view) return `<div class="thumb"></div>`;
    return `<img class="thumb" loading="lazy" alt="" src="${esc(this._view.mealie_url)}/api/media/recipes/${esc(recipe.id)}/images/min-original.webp" onerror="this.style.visibility='hidden'">`;
  }

  _ruleNames() {
    const names = {};
    for (const rule of (this._state?.settings?.rules || [])) names[rule.id] = rule.name;
    for (const line of (this._view?.rules || [])) names[line.id] = line.name;
    return names;
  }

  _planHtml() {
    const view = this._view;
    if (!view) return "";
    const changed = view.slots.some((slot) => slot.changed);
    const ai = this._state.ai;
    const rules = view.rules.map((line) => {
      const bound = line.max != null ? `${line.min}–${line.max}` : `${line.min}+`;
      return `<span class="rule ${line.state}" title="${esc(this.t(line.kind))}: ${esc(this.t("state_" + line.state))}">${line.state === "ok" ? "✓" : line.state === "short" ? "…" : "!"} ${esc(line.name)} ${line.count}/${bound}</span>`;
    }).join("");
    const names = this._ruleNames();
    const byDay = {};
    for (const slot of view.slots) (byDay[slot.date] = byDay[slot.date] || []).push(slot);
    const days = [];
    for (let i = 0; i < 7; i++) {
      const date = addDays(view.week, i);
      const slots = byDay[date] || [];
      const d = weekday(date);
      days.push(`<section class="day"><h3><b>${esc(this.t("daysLong")[d])}</b><span>${short(date)}</span></h3>
        ${slots.length ? slots.map((slot) => this._slotHtml(slot, names)).join("") : `<div class="muted">—</div>`}</section>`);
    }
    const planned = view.slots.some((slot) => slot.recipe);
    return `
      <div class="bar">${this._weekNav()}<span class="grow"></span>
        ${ai ? `<button class="chip" data-action="mode" aria-pressed="${this._mode() === "ai"}">${icon("magic", 16)} ${this.t(this._mode() === "ai" ? "ai" : "local")}</button>` : ""}
        <label class="check"><input type="checkbox" id="replaceSaved" ${this._replaceSaved ? "checked" : ""}> ${this.t("replaceSaved")}</label>
        <button class="btn primary" data-action="generate">${icon("magic")} ${this.t(planned ? "again" : "generate")}</button>
        <button class="btn" data-action="save" ${changed ? "" : "disabled"}>${icon("save")} ${this.t("save")}</button>
      </div>
      ${view.notice ? `<div class="notice">${esc(this.t("notice_" + view.notice))}</div>` : ""}
      ${this._moving ? `<div class="notice">${esc(this.t("moveHint"))}</div>` : ""}
      <div class="rules">${rules}</div>
      ${planned ? "" : `<div class="empty">${esc(this.t("nothingPlanned"))}</div>`}
      <div class="week">${days.join("")}</div>`;
  }

  _mode() {
    return storage("mealie-planner-mode") || this._state.mode;
  }

  _slotHtml(slot, names) {
    const recipe = slot.recipe;
    const moving = this._moving === slot.key;
    const target = this._moving && !moving;
    const meal = `<div class="meal">${esc(this.t("meal_" + slot.meal))}
      ${slot.saved ? `<span class="state saved">✓ ${this.t("saved")}</span>` : slot.changed ? `<span class="state changed">● ${this.t("changed")}</span>` : ""}</div>`;
    const cls = `slot${moving ? " moving" : ""}${target ? " target" : ""}`;
    if (!recipe) {
      return `<div class="${cls}" data-slot="${esc(slot.key)}" ${target ? `data-action="drop"` : ""}><div class="body">${meal}
        <div class="emptyslot"><span>${this.t("empty")}</span>
        <button class="btn small" data-action="pick" data-slot="${esc(slot.key)}">${icon("plus", 16)} ${this.t("add")}</button></div></div></div>`;
    }
    const url = this._recipeUrl(recipe);
    const flags = (recipe.flags || []).map((flag) => `<span class="badge">${esc(names[flag] || flag)}</span>`).join("");
    const sale = recipe.sale && recipe.sale.length ? `<span class="badge sale" title="${esc(recipe.sale.join(", "))}">🏷 ${esc(this.t("onSale", { n: recipe.sale.length }))}</span>` : "";
    return `<div class="${cls}" data-slot="${esc(slot.key)}" ${target ? `data-action="drop"` : ""}>
      ${this._thumb(recipe)}
      <div class="body">${meal}
        ${url ? `<a class="name" href="${esc(url)}" target="_blank" rel="noreferrer">${esc(recipe.name)}</a>` : `<span class="name">${esc(recipe.name)}</span>`}
        <div class="badges">${flags}${sale}</div>
        ${slot.reason ? `<div class="reason">${esc(slot.reason)}</div>` : ""}
        <div class="tools">
          <button data-action="pick" data-slot="${esc(slot.key)}" title="${this.t("change")}">${icon("edit")}</button>
          <button data-action="lock" data-slot="${esc(slot.key)}" class="${slot.locked ? "on" : ""}" title="${this.t(slot.locked ? "unlock" : "lock")}">${icon(slot.locked ? "lock" : "unlock")}</button>
          <button data-action="move" data-slot="${esc(slot.key)}" class="${moving ? "on" : ""}" title="${this.t("move")}">${icon("swap")}</button>
          <button data-action="clearslot" data-slot="${esc(slot.key)}" title="${this.t("clear")}">${icon("delete")}</button>
        </div>
      </div></div>`;
  }

  async _openPicker(slotKey, query = "") {
    const [date, meal] = slotKey.split("|");
    const title = `${this.t("daysLong")[weekday(date)]} ${short(date)} · ${this.t("meal_" + meal)}`;
    this._dialog.innerHTML = `<div class="dhead"><h2>${esc(this.t("pickTitle", { slot: title }))}</h2>
      <button class="round" data-action="closedialog">${icon("close")}</button></div>
      <div class="dbody"><div class="filters"><input type="search" id="pickquery" data-slot="${esc(slotKey)}" placeholder="${esc(this.t("search"))}" value="${esc(query)}"></div>
      <div id="picklist"><div class="spinner" style="margin:auto"></div></div></div>`;
    if (!this._dialog.open) this._dialog.showModal();
    this.shadowRoot.getElementById("pickquery").focus();
    await this._fillPicker(slotKey, query);
  }

  async _fillPicker(slotKey, query) {
    const token = (this._pickToken = (this._pickToken || 0) + 1);
    let items;
    try {
      items = await this._ws("recipes/pick", { week: this._week, slot: slotKey, query: query || null });
    } catch (error) {
      this._toast(error.message);
      return;
    }
    if (token !== this._pickToken) return;
    const names = this._ruleNames();
    const list = this.shadowRoot.getElementById("picklist");
    if (!list) return;
    list.innerHTML = items.length ? items.map((item) => `
      <button class="pick" data-action="choose-recipe" data-slot="${esc(slotKey)}" data-recipe="${esc(item.id)}">
        ${this._thumb(item)}
        <div class="main"><div class="title">${esc(item.name)}</div>
          <div class="badges">${item.needed ? `<span class="badge need">${this.t("needed")}</span>` : ""}
          ${(item.flags || []).map((flag) => `<span class="badge">${esc(names[flag] || flag)}</span>`).join("")}
          ${item.sale.length ? `<span class="badge sale" title="${esc(item.sale.join(", "))}">🏷 ${esc(this.t("onSale", { n: item.sale.length }))}</span>` : ""}</div>
        </div></button>`).join("") : `<div class="empty">${this.t("noRecipes")}</div>`;
  }

  // --- Products -------------------------------------------------------------
  _productsHtml() {
    const view = this._view;
    if (!view) return "";
    const items = view.basket || [];
    const nav = `<div class="bar">${this._weekNav()}<span class="grow"></span>`;
    if (!items.length) return `${nav}</div><div class="empty">${esc(this.t("basketEmpty"))}</div>`;
    const lists = view.lists || { available: false, lists: [] };
    const checked = items.filter((item) => item.checked);
    const sum = checked.reduce((total, item) => total + (item.offer ? item.offer.price : 0), 0);
    // The three shops first, then shops HomeBasket Lists keeps products under, then none.
    const groups = { lidl: [], kaufland: [], billa: [] };
    const names = {};
    for (const item of items) {
      const shop = item.shop || "none";
      if (item.shop_name) names[shop] = item.shop_name;
      (groups[shop] = groups[shop] || []).push(item);
    }
    const none = groups.none || [];
    delete groups.none;
    groups.none = none;
    const listSelect = lists.available && lists.lists.length > 1
      ? `<select id="listpick">${lists.lists.map((list) => `<option value="${esc(list.entry_id)}" ${(this._listEntry || lists.entry_id) === list.entry_id ? "selected" : ""}>${esc(list.name)}</option>`).join("")}</select>` : "";
    const html = [`${nav}
      <button class="btn small" data-action="select-sale">${this.t("selectSale")}</button>
      <button class="btn small" data-action="select-none">${this.t("selectNone")}</button>
      ${listSelect}
      <button class="btn primary" data-action="add-list" ${checked.length && lists.available ? "" : "disabled"}>${icon("basket")} ${this.t("addToList", { n: checked.length })}</button></div>
      ${lists.available ? "" : `<div class="notice">${esc(this.t("listMissing"))}</div>`}
      ${sum ? `<p class="muted">${esc(this.t("estimate", { sum: money(sum) }))}</p>` : ""}`];
    for (const [chain, members] of Object.entries(groups)) {
      if (!members.length) continue;
      const color = CHAIN_COLORS[chain] || "var(--mp-muted)";
      html.push(`<section class="group"><h3><span class="dot" style="background:${color}"></span>${esc(CHAINS[chain] || names[chain] || this.t("noShop"))}
        <span class="muted">(${members.length})</span></h3>${members.map((item) => this._itemHtml(item)).join("")}</section>`);
    }
    return html.join("");
  }

  _amount(item) {
    if (!item.quantity) return "";
    const value = Number.isInteger(item.quantity) ? item.quantity : Number(item.quantity).toFixed(2).replace(/\.?0+$/, "");
    return `${value}${item.unit ? " " + item.unit : ""}${item.unknown_quantity ? " +" : ""}`;
  }

  _priceHtml(offer) {
    if (!offer) return `<div class="price muted">${this.t("noOffer")}</div>`;
    const dates = offer.valid_from || offer.valid_to ? `${short(offer.valid_from)}–${short(offer.valid_to)}` : this.t("noDates");
    return `<div class="price"><b>${money(offer.price)} €</b>${offer.old_price ? `<s>${money(offer.old_price)}</s>` : ""}
      ${offer.discount_pct ? `<span class="off">−${offer.discount_pct}%</span>` : ""}<span class="dates">${esc(dates)}</span></div>`;
  }

  _itemHtml(item) {
    const offer = item.offer;
    const sub = [this._amount(item), item.recipes.length ? `${this.t("recipesFor")} ${item.recipes.join(", ")}` : ""].filter(Boolean).join(" · ");
    const offerLine = offer ? `${offer.name}${offer.quantity ? " · " + offer.quantity : ""}${item.picked ? " · " + this.t("byHand") : ""}`
      : item.home_zone ? this.t("homeShop") : (item.picked ? this.t("byHand") : "");
    return `<div class="item" data-action="details" data-key="${esc(item.key)}">
      <input type="checkbox" data-action="tick" data-key="${esc(item.key)}" ${item.checked ? "checked" : ""} aria-label="${esc(item.name)}">
      <div class="main"><div class="title">${esc(item.name)}</div>
        <div class="sub">${esc(sub)}</div>${offerLine ? `<div class="sub">${esc(offerLine)}</div>` : ""}</div>
      ${this._priceHtml(offer)}</div>`;
  }

  async _openDetails(key) {
    const item = (this._view.basket || []).find((entry) => entry.key === key);
    if (!item) return;
    const offer = item.offer;
    this._dialog.innerHTML = `<div class="dhead"><h2>${esc(item.name)}</h2><button class="round" data-action="closedialog">${icon("close")}</button></div>
      <div class="dbody">
        <div class="muted">${esc(this._amount(item))} ${item.recipes.length ? "· " + esc(this.t("recipesFor")) + " " + esc(item.recipes.join(", ")) : ""}</div>
        ${offer ? `<div class="current">${offer.image ? `<img src="${esc(offer.image)}" alt="" ${this._zoomAttrs(offer)} onerror="this.style.display='none'">` : ""}
          <div class="main" style="flex:1"><div class="title"><b>${esc(CHAINS[offer.chain])}</b> · ${esc(offer.name)}</div>
          <div class="muted">${esc(this._offerMeta(offer))}</div>${this._priceHtml(offer)}
          ${offer.url ? `<a class="muted" href="${esc(offer.url)}" target="_blank" rel="noreferrer">${icon("open", 14)}</a>` : ""}</div></div>`
          : `<div class="current">${esc(this.t("noOffer"))}</div>`}
        <div class="bar"><button class="btn small" data-action="choose-offer" data-key="${esc(key)}" data-offer="none">${this.t("noShop")}</button>
          ${item.picked ? `<button class="btn small" data-action="choose-offer" data-key="${esc(key)}" data-offer="">${this.t("auto")}</button>` : ""}</div>
        <div class="simhead">${this.t("similar")}</div><div id="alts"><div class="spinner" style="margin:auto"></div></div>
      </div>`;
    if (!this._dialog.open) this._dialog.showModal();
    let alts;
    try {
      alts = await this._ws("shopping/alternatives", { week: this._week, key });
    } catch (error) {
      this._toast(error.message);
      return;
    }
    const box = this.shadowRoot.getElementById("alts");
    if (!box) return;
    let group = null;
    box.innerHTML = alts.length ? alts.map((alt) => {
      const head = alt.similarity !== group ? `<div class="simhead">${esc(this.t("sim_" + alt.similarity))}</div>` : "";
      group = alt.similarity;
      return `${head}<div class="alt">${alt.image ? `<img src="${esc(alt.image)}" alt="" loading="lazy" ${this._zoomAttrs(alt)} onerror="this.style.visibility='hidden'">` : ""}
        <div class="main"><div class="title"><b>${esc(CHAINS[alt.chain])}</b> · ${esc(alt.name)}</div><div class="sub muted">${esc(this._offerMeta(alt))}</div></div>
        ${this._priceHtml(alt)}<button class="btn small" data-action="choose-offer" data-key="${esc(key)}" data-offer="${esc(alt.id)}">${this.t("choose")}</button></div>`;
    }).join("") : `<div class="muted">—</div>`;
  }

  _zoomAttrs(offer) {
    const page = offer.page_image && offer.page_image !== offer.image ? offer.page_image : "";
    return `class="zoomable" data-action="zoom" data-src="${esc(offer.image)}" data-page="${esc(page)}" data-title="${esc(`${CHAINS[offer.chain] || ""} · ${offer.name}`)}"`;
  }

  _openZoom(src, page, title, showingPage = false) {
    const shown = showingPage ? page : src;
    const other = page ? `<button class="btn small" data-action="zoom-other">${this.t(showingPage ? "zoomProduct" : "zoomPage")}</button>` : "";
    this._zoom.innerHTML = `<div class="zbar"><b>${esc(title)}</b>${other}
      <button class="round" data-action="zoom-close" aria-label="${this.t("close")}">${icon("close")}</button></div>
      <img src="${esc(shown)}" alt="${esc(title)}" data-action="zoom-close">`;
    this._zoomState = { src, page, title, showingPage };
    if (!this._zoom.open) this._zoom.showModal();
  }

  _offerMeta(offer) {
    const parts = [];
    if (offer.quantity) parts.push(offer.quantity);
    if (offer.unit_price) parts.push(this.t("unitPrice", { price: money(offer.unit_price), unit: this.t("unit_" + offer.unit_base) }));
    if (offer.conditions) parts.push(offer.conditions);
    if (offer.page) parts.push(`${this.t("page")} ${offer.page}`);
    return parts.join(" · ");
  }

  // --- Offers ---------------------------------------------------------------
  _filtered() {
    const f = this._filters;
    const today = this._offers.today || todayIso();
    const weekStart = this._week;
    const weekEnd = weekStart ? addDays(weekStart, 6) : today;
    const text = f.text.trim().toLowerCase();
    let list = this._offers.offers.filter((offer) => {
      if (f.chains.length && !f.chains.includes(offer.chain)) return false;
      if (f.categories.length && !f.categories.includes(offer.category || "other_food")) return false;
      if (f.discount && (offer.discount_pct || 0) < f.discount) return false;
      if (text && !`${offer.name} ${offer.brand || ""} ${offer.food || ""}`.toLowerCase().includes(text)) return false;
      const from = offer.valid_from || "0000";
      const to = offer.valid_to || "9999";
      if (f.date === "today" && (from > today || to < today)) return false;
      if (f.date === "week" && (from > weekEnd || to < weekStart)) return false;
      return true;
    });
    const by = {
      discount: (a, b) => (b.discount_pct || 0) - (a.discount_pct || 0),
      price: (a, b) => a.price - b.price,
      unit: (a, b) => (a.unit_price ?? 1e9) - (b.unit_price ?? 1e9),
      name: (a, b) => a.name.localeCompare(b.name, this._lang),
      expiry: (a, b) => String(a.valid_to || "9999").localeCompare(String(b.valid_to || "9999")),
      chain: (a, b) => a.chain.localeCompare(b.chain) || a.name.localeCompare(b.name, this._lang),
    }[f.sort] || (() => 0);
    list = list.slice().sort(by);
    return list;
  }

  _sourcesHtml() {
    const data = this._offers;
    const admin = this._state.admin;
    const cards = Object.keys(CHAINS).map((chain) => {
      const sources = (data.sources[chain] || []).slice().sort((a, b) => (a.kind === "web" ? -1 : 1));
      const config = data.chains[chain] || {};
      const lines = sources.map((source) => {
        const tokens = source.tokens && (source.tokens.prompt || source.tokens.completion) ? ` · ${this.t("tokens", { p: source.tokens.prompt, c: source.tokens.completion })}` : "";
        const dates = source.valid_from || source.valid_to ? ` · ${short(source.valid_from)}–${short(source.valid_to)}` : "";
        const label = source.kind === "web" ? this.t("web") : `${this.t("brochure")}: ${source.title || ""}`;
        return `<div class="line"><span>${esc(label)}${esc(dates)}</span>
          ${source.error ? `<span class="err" title="${esc(source.error)}">${this.t("error")}</span>` : `<span>${esc(this.t("count", { n: source.count ?? 0 }))}${esc(tokens)}</span>`}
          ${admin && source.kind === "brochure" ? `<button class="btn small" data-action="rescan" data-source="${esc(source.id)}" title="${this.t("rescan")}">${icon("refresh", 14)}</button>` : ""}</div>`;
      }).join("");
      return `<div class="source"><h4><span class="dot" style="background:${CHAIN_COLORS[chain]}"></span>${CHAINS[chain]}
        <span class="muted">${config.web ? this.t("web") : ""}${config.web && config.brochures ? " + " : ""}${config.brochures ? this.t("brochure") : ""}</span></h4>
        ${lines || `<div class="muted">—</div>`}</div>`;
    }).join("");
    return cards;
  }

  _offersHtml() {
    const data = this._offers;
    if (!data) return "";
    const f = this._filters;
    const admin = this._state.admin;
    const list = this._filtered();
    const shown = list.slice(0, f.limit);
    const usage = data.usage || {};
    const chainChips = Object.entries(CHAINS).map(([key, name]) => `<button class="chip" data-action="fchain" data-chain="${key}" aria-pressed="${f.chains.includes(key)}">${name}</button>`).join("");
    const present = new Set(data.offers.map((offer) => offer.category || "other_food"));
    const catChips = CATEGORIES.filter((key) => present.has(key)).map((key) => `<button class="chip" data-action="fcat" data-cat="${key}" aria-pressed="${f.categories.includes(key)}">${this.t("cat_" + key)}</button>`).join("");
    const option = (value, label, current) => `<option value="${value}" ${String(current) === String(value) ? "selected" : ""}>${esc(label)}</option>`;
    return `
      <div class="bar"><h3 style="margin:0">${this.t("status")}</h3><span class="grow"></span>
        <span class="muted">${esc(this.t("tokens", { p: usage.prompt || 0, c: usage.completion || 0 }))}</span>
        ${admin ? `<button class="btn small" data-action="probe">${this.t("probe")}</button>` : ""}
        ${admin && this._state.ai ? `<button class="btn small" data-action="addbrochure">${icon("plus", 16)} ${this.t("addBrochure")}</button>` : ""}
        ${admin ? `<button class="btn primary small" data-action="refresh" ${data.refreshing ? "disabled" : ""}>${data.refreshing ? `<span class="spinner"></span> ${this.t("refreshing")}` : `${icon("refresh", 16)} ${this.t("refresh")}`}</button>` : ""}
      </div>
      <div class="sources">${this._sourcesHtml()}</div>
      <div class="filters">
        <input type="search" id="ftext" placeholder="${esc(this.t("filterText"))}" value="${esc(f.text)}">
        <select id="fdate">${option("today", this.t("today"), f.date)}${option("week", `${this.t("planWeek")} ${short(this._week)}–${short(addDays(this._week, 6))}`, f.date)}${option("any", this.t("anyDate"), f.date)}</select>
        <select id="fdiscount">${[0, 10, 20, 30, 40, 50].map((n) => option(n, n ? `${this.t("minDiscount")} ≥ ${n}%` : `${this.t("minDiscount")}: ${this.t("all")}`, f.discount)).join("")}</select>
        <select id="fsort">${["discount", "price", "unit", "name", "expiry", "chain"].map((key) => option(key, this.t("sort_" + key), f.sort)).join("")}</select>
      </div>
      <div class="filters">${chainChips}<span style="width:8px"></span>${catChips}</div>
      <p class="muted">${esc(this.t("shown", { n: shown.length, total: list.length }))}</p>
      ${shown.length ? `<div class="grid">${shown.map((offer) => this._offerCard(offer)).join("")}</div>` : `<div class="empty">${this.t("noOffers")}</div>`}
      ${list.length > shown.length ? `<div class="empty"><button class="btn" data-action="more">${this.t("more")}</button></div>` : ""}`;
  }

  _offerCard(offer) {
    const dates = offer.valid_from || offer.valid_to ? `${this.t("validity")} ${short(offer.valid_from)}–${short(offer.valid_to)}` : this.t("noDates");
    const lists = this._view ? this._view.lists : this._state.lists;
    return `<article class="offer">
      <div class="img">${offer.image ? `<img src="${esc(offer.image)}" alt="" loading="lazy" ${this._zoomAttrs(offer)} onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'ph',textContent:'🛒'}))">` : `<span class="ph">🛒</span>`}</div>
      <span class="shop ${offer.chain}" style="background:${CHAIN_COLORS[offer.chain]}">${CHAINS[offer.chain]}</span>
      ${offer.discount_pct ? `<span class="disc">−${offer.discount_pct}%</span>` : ""}
      <div class="info"><div class="oname">${esc(offer.name)}</div>
        <div class="meta">${esc(this._offerMeta(offer))}</div>
        <div class="meta">${esc(dates)}${offer.category ? " · " + esc(this.t("cat_" + offer.category)) : ""}</div>
        <div class="row"><b>${money(offer.price)} €</b>${offer.old_price ? `<s>${money(offer.old_price)} €</s>` : ""}
        ${lists && lists.available ? `<button class="round" data-action="offer-add" data-offer="${esc(offer.id)}" title="${esc(this.t("addToList", { n: 1 }))}">${icon("plus")}</button>` : ""}</div>
      </div></article>`;
  }

  _openBrochureDialog() {
    this._dialog.innerHTML = `<div class="dhead"><h2>${this.t("addBrochure")}</h2><button class="round" data-action="closedialog">${icon("close")}</button></div>
      <div class="dbody">
        <label class="field">${this.t("chain")}<select id="bchain">${Object.entries(CHAINS).map(([key, name]) => `<option value="${key}">${name}</option>`).join("")}</select></label>
        <label class="field">${this.t("url")}<input id="burl" type="url" placeholder="https://…"></label>
        <label class="field">${this.t("title")}<input id="btitle"></label>
        <div class="bar"><label class="field">${this.t("from")}<input id="bfrom" type="date"></label><label class="field">${this.t("to")}<input id="bto" type="date"></label></div>
        <p class="muted">${this.t("reading")}</p>
        <div class="bar"><span class="grow"></span><button class="btn primary" data-action="readbrochure">${this.t("read")}</button></div>
      </div>`;
    this._dialog.showModal();
  }

  // --- Settings -------------------------------------------------------------
  _settingsHtml() {
    const s = this._settings;
    if (!s) return "";
    const admin = this._state.admin;
    const org = this._organizers || { tags: [], categories: [], foods: [] };
    const lists = `<datalist id="dl-tags">${org.tags.map((v) => `<option value="${esc(v)}">`).join("")}</datalist>
      <datalist id="dl-categories">${org.categories.map((v) => `<option value="${esc(v)}">`).join("")}</datalist>`;
    const rules = s.rules.map((rule, index) => `
      <div class="ruleedit" data-index="${index}">
        <label class="field">${this.t("ruleName")}<input data-field="name" value="${esc(rule.name)}"></label>
        <label class="field">&nbsp;<select data-field="kind"><option value="required" ${rule.kind === "required" ? "selected" : ""}>${this.t("required")}</option><option value="preferred" ${rule.kind === "preferred" ? "selected" : ""}>${this.t("preferred")}</option></select></label>
        <label class="field">${this.t("min")}<input data-field="min" type="number" min="0" max="21" value="${rule.min}"></label>
        <label class="field">${this.t("max")}<input data-field="max" type="number" min="0" max="21" value="${rule.max ?? ""}"></label>
        <label class="field">&nbsp;<select data-field="mode"><option value="contains" ${rule.mode === "contains" ? "selected" : ""}>${this.t("contains")}</option><option value="excludes" ${rule.mode === "excludes" ? "selected" : ""}>${this.t("excludes")}</option></select></label>
        <label class="field wide">${this.t("tags")}<input data-field="tags" list="dl-tags" value="${esc(rule.tags.join(", "))}"></label>
        <label class="field wide">${this.t("categories")}<input data-field="categories" list="dl-categories" value="${esc(rule.categories.join(", "))}"></label>
        <label class="field wide">${this.t("foods")}<textarea data-field="foods" rows="2">${esc(rule.foods.join(", "))}</textarea></label>
        ${admin ? `<div class="actions">
          <button class="round" data-action="rule-up" data-index="${index}" ${index ? "" : "disabled"}>${icon("up")}</button>
          <button class="round" data-action="rule-down" data-index="${index}" ${index < s.rules.length - 1 ? "" : "disabled"}>${icon("down")}</button>
          <button class="round" data-action="rule-delete" data-index="${index}">${icon("delete")}</button></div>` : ""}
      </div>`).join("");
    const head = MEALS.map((meal) => `<span class="muted">${this.t("meal_" + meal)}</span>`).join("");
    const days = [0, 1, 2, 3, 4, 5, 6].map((day) => `<b>${this.t("daysLong")[day]}</b>${MEALS.map((meal) =>
      `<input type="checkbox" data-day="${day}" data-meal="${meal}" ${(s.slots[String(day)] || []).includes(meal) ? "checked" : ""} ${admin ? "" : "disabled"}>`).join("")}`).join("");
    return `${lists}
      ${admin ? "" : `<div class="notice">${this.t("adminOnly")}</div>`}
      <div class="notice">${this.t("moreOptions")}
        ${admin ? ` <a href="/config/integrations/integration/mealie_planner">${this.t("openOptions")}</a>` : ""}</div>
      <section class="card"><h3>${this.t("rules")}</h3>${rules}
        ${admin ? `<div class="bar"><button class="btn small" data-action="rule-add">${icon("plus", 16)} ${this.t("addRule")}</button>
        <button class="btn small" data-action="rule-presets">${this.t("presets")}</button></div>` : ""}</section>
      <section class="card"><h3>${this.t("meals")}</h3><div class="days"><span></span>${head}${days}</div></section>
      <section class="card"><label class="field">${this.t("recent")}<input id="recent" type="number" min="0" max="8" value="${s.recent_weeks}" ${admin ? "" : "disabled"} style="max-width:120px"></label></section>
      ${admin ? `<div class="bar"><span class="grow"></span><button class="btn primary" data-action="save-settings">${icon("save")} ${this.t("saveSettings")}</button></div>` : ""}`;
  }

  _readRules() {
    const split = (value) => String(value || "").split(",").map((part) => part.trim()).filter(Boolean);
    this.shadowRoot.querySelectorAll(".ruleedit").forEach((node) => {
      const rule = this._settings.rules[Number(node.dataset.index)];
      const get = (field) => node.querySelector(`[data-field="${field}"]`).value;
      rule.name = get("name").trim();
      rule.kind = get("kind");
      rule.mode = get("mode");
      rule.min = Number(get("min") || 0);
      rule.max = get("max") === "" ? null : Number(get("max"));
      rule.tags = split(get("tags"));
      rule.categories = split(get("categories"));
      rule.foods = split(get("foods"));
    });
    const slots = {};
    for (let day = 0; day < 7; day++) slots[String(day)] = [];
    this.shadowRoot.querySelectorAll("[data-day]").forEach((box) => { if (box.checked) slots[box.dataset.day].push(box.dataset.meal); });
    this._settings.slots = slots;
    const recent = this.shadowRoot.getElementById("recent");
    if (recent) this._settings.recent_weeks = Number(recent.value || 0);
  }

  // --- Events ---------------------------------------------------------------
  async _setView(promise) {
    const view = await promise;
    if (view) {
      this._view = view;
      this._render();
    }
    return view;
  }

  async _click(event) {
    const target = event.target.closest("[data-action]");
    if (!target) return;
    const action = target.dataset.action;
    if (action === "tick") { event.stopPropagation(); return; }
    const week = this._week;
    switch (action) {
      case "tab":
        this._tab = target.dataset.tab;
        storage("mealie-planner-tab", this._tab);
        this._moving = null;
        this._renderTabs();
        await this._run(null, () => this._load());
        break;
      case "week":
        this._week = addDays(this._week, Number(target.dataset.step));
        this._moving = null;
        await this._run(target, () => this._load());
        break;
      case "mode":
        storage("mealie-planner-mode", this._mode() === "ai" ? "local" : "ai");
        this._render();
        break;
      case "generate":
        await this._run(target, () => this._setView(this._ws("plan/generate", { week, mode: this._mode(), replace_saved: !!this._replaceSaved })));
        break;
      case "save": {
        const view = await this._run(target, () => this._setView(this._ws("plan/save", { week })));
        if (view && view.saved) this._toast(this.t("savedMsg", view.saved));
        break;
      }
      case "pick":
        this._moving = null;
        await this._openPicker(target.dataset.slot);
        break;
      case "choose-recipe":
        this._dialog.close();
        await this._run(null, () => this._setView(this._ws("plan/update_slot", { week, slot: target.dataset.slot, recipe_id: target.dataset.recipe })));
        break;
      case "lock": {
        const slot = this._view.slots.find((entry) => entry.key === target.dataset.slot);
        await this._run(target, () => this._setView(this._ws("plan/update_slot", { week, slot: slot.key, locked: !slot.locked })));
        break;
      }
      case "clearslot":
        await this._run(target, () => this._setView(this._ws("plan/update_slot", { week, slot: target.dataset.slot, recipe_id: null })));
        break;
      case "move":
        this._moving = this._moving === target.dataset.slot ? null : target.dataset.slot;
        this._render();
        break;
      case "drop": {
        const source = this._moving;
        this._moving = null;
        await this._run(null, () => this._setView(this._ws("plan/move_slot", { week, source, target: target.dataset.slot })));
        break;
      }
      case "zoom":
        event.stopPropagation();
        this._openZoom(target.dataset.src, target.dataset.page, target.dataset.title);
        break;
      case "zoom-other": {
        const state = this._zoomState;
        this._openZoom(state.src, state.page, state.title, !state.showingPage);
        break;
      }
      case "zoom-close":
        this._zoom.close();
        break;
      case "closedialog":
        this._dialog.close();
        break;
      case "details":
        await this._openDetails(target.dataset.key);
        break;
      case "choose-offer": {
        const offer = target.dataset.offer;
        this._dialog.close();
        await this._run(null, () => this._setView(this._ws("shopping/choose", { week, key: target.dataset.key, offer_id: offer === "" ? null : offer })));
        break;
      }
      case "select-sale": {
        const keys = this._view.basket.filter((item) => item.offer).map((item) => item.key);
        await this._run(target, () => this._setView(this._ws("shopping/check", { week, keys, checked: true })));
        break;
      }
      case "select-none": {
        const keys = this._view.basket.map((item) => item.key);
        await this._run(target, () => this._setView(this._ws("shopping/check", { week, keys, checked: false })));
        break;
      }
      case "add-list": {
        const keys = this._view.basket.filter((item) => item.checked).map((item) => item.key);
        const result = await this._run(target, () => this._ws("shopping/add", { week, keys, entry_id: this._listEntry || null }));
        if (result) {
          this._toast(this.t("added", { n: result.added }));
          await this._setView(this._ws("shopping/check", { week, keys, checked: false }));
        }
        break;
      }
      case "offer-add": {
        const result = await this._run(target, () => this._ws("offer/add_to_list", { offer_id: target.dataset.offer, entry_id: this._listEntry || null }));
        if (result) this._toast(this.t("added", { n: result.added }));
        break;
      }
      case "fchain":
      case "fcat": {
        const list = action === "fchain" ? this._filters.chains : this._filters.categories;
        const value = action === "fchain" ? target.dataset.chain : target.dataset.cat;
        const at = list.indexOf(value);
        if (at >= 0) list.splice(at, 1); else list.push(value);
        this._filters.limit = 60;
        this._saveFilters();
        this._render();
        break;
      }
      case "more":
        this._filters.limit += 60;
        this._render();
        break;
      case "refresh":
        await this._run(target, async () => {
          await this._ws("offers/refresh");
          this._offers = await this._ws("offers");
          this._offers.refreshing = true;
          this._render();
          this._watch();
        });
        break;
      case "rescan":
        await this._run(target, async () => {
          await this._ws("offers/rescan", { source_id: target.dataset.source });
          this._offers = await this._ws("offers");
          this._render();
        });
        break;
      case "addbrochure":
        this._openBrochureDialog();
        break;
      case "readbrochure": {
        const root = this.shadowRoot;
        const data = {
          chain: root.getElementById("bchain").value,
          url: root.getElementById("burl").value.trim(),
          title: root.getElementById("btitle").value.trim() || null,
          valid_from: root.getElementById("bfrom").value || null,
          valid_to: root.getElementById("bto").value || null,
        };
        const result = await this._run(target, () => this._ws("offers/add_url", data));
        if (result) {
          this._dialog.close();
          this._offers = await this._ws("offers");
          this._render();
        }
        break;
      }
      case "probe": {
        const result = await this._run(target, () => this._ws("offers/probe"));
        if (!result) break;
        this._dialog.innerHTML = `<div class="dhead"><h2>${this.t("probe")}</h2><button class="round" data-action="closedialog">${icon("close")}</button></div>
          <div class="dbody"><pre>${esc(JSON.stringify(result, null, 2))}</pre></div>`;
        this._dialog.showModal();
        break;
      }
      case "rule-add":
        this._readRules();
        this._settings.rules.push({ id: `r${Date.now().toString(36)}`, name: "", kind: "preferred", min: 1, max: null, mode: "contains", tags: [], categories: [], foods: [] });
        this._render();
        break;
      case "rule-presets": {
        this._readRules();
        const have = new Set(this._settings.rules.map((rule) => rule.id));
        for (const preset of this._state.presets || []) if (!have.has(preset.id)) this._settings.rules.push(JSON.parse(JSON.stringify(preset)));
        this._render();
        break;
      }
      case "rule-delete":
      case "rule-up":
      case "rule-down": {
        this._readRules();
        const index = Number(target.dataset.index);
        const rules = this._settings.rules;
        if (action === "rule-delete") rules.splice(index, 1);
        else {
          const other = action === "rule-up" ? index - 1 : index + 1;
          [rules[index], rules[other]] = [rules[other], rules[index]];
        }
        this._render();
        break;
      }
      case "save-settings":
        this._readRules();
        await this._run(target, async () => {
          this._settings = await this._ws("settings/set", { settings: this._settings });
          this._state.settings = JSON.parse(JSON.stringify(this._settings));
          this._toast(this.t("settingsSaved"));
          this._render();
        });
        break;
      default:
        break;
    }
  }

  async _change(event) {
    const node = event.target;
    if (node.dataset && node.dataset.action === "tick") {
      await this._run(null, () => this._setView(this._ws("shopping/check", { week: this._week, keys: [node.dataset.key], checked: node.checked })));
      return;
    }
    switch (node.id) {
      case "replaceSaved":
        this._replaceSaved = node.checked;
        break;
      case "listpick":
        this._listEntry = node.value;
        break;
      case "fdate":
      case "fdiscount":
      case "fsort": {
        const key = { fdate: "date", fdiscount: "discount", fsort: "sort" }[node.id];
        this._filters[key] = key === "discount" ? Number(node.value) : node.value;
        this._filters.limit = 60;
        this._saveFilters();
        this._render();
        break;
      }
      default:
        break;
    }
  }

  _input(event) {
    const node = event.target;
    if (node.id === "ftext") {
      this._filters.text = node.value;
      this._filters.limit = 60;
      clearTimeout(this._typing);
      this._typing = setTimeout(() => {
        this._render();
        const input = this.shadowRoot.getElementById("ftext");
        if (input) { input.focus(); input.setSelectionRange(input.value.length, input.value.length); }
      }, 250);
    } else if (node.id === "pickquery") {
      clearTimeout(this._typing);
      this._typing = setTimeout(() => this._fillPicker(node.dataset.slot, node.value.trim()), 250);
    }
  }

  _saveFilters() {
    const { chains, categories, date, discount, sort } = this._filters;
    storage("mealie-planner-filters", JSON.stringify({ chains, categories, date, discount, sort }));
  }
}

customElements.define("mealie-planner-panel", MealiePlannerPanel);
