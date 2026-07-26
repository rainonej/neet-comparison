(() => {
  const D = window.STORY_DATA || {};
  const scarcity = D.scarcity || {};
  const razor = D.razor || {};
  const tn = D.tn_repeater_time_series || D.ticket_cost?.admitted_composition?.post_neet_years || [];

  const LOCALE_KEY = 'neet-essay-locale';
  const DICT = {
    'en-IN': {
      grade12: 'Class XII',
      centres: 'exam centres',
      emi: 'monthly installments (EMIs)',
      'govt-school': 'government schools',
      'daily-wage': 'daily-wage earners',
      money: {
        550000: '₹5.5 lakh borrowed',
        150000: '₹1.5 lakh borrowed',
        1890000: '₹18.9 lakh',
        2500000: '₹25 lakh',
        800000: '₹8 lakh',
        250000: '₹2.5 lakh'
      }
    },
    'en-US': {
      grade12: 'Grade 12',
      centres: 'test centers',
      emi: 'monthly coaching installments',
      'govt-school': 'public/government schools',
      'daily-wage': 'workers paid by the day',
      money: {
        550000: '₹550,000 borrowed',
        150000: '₹150,000 borrowed',
        1890000: '₹1,890,000',
        2500000: '₹2,500,000',
        800000: '₹800,000',
        250000: '₹250,000'
      }
    }
  };

  const detectLocale = () => {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get('lang') || params.get('locale');
    if (fromQuery === 'en-US' || fromQuery === 'en-IN') return fromQuery;
    try {
      const saved = localStorage.getItem(LOCALE_KEY);
      if (saved === 'en-US' || saved === 'en-IN') return saved;
    } catch (_) { /* ignore */ }
    const nav = (navigator.language || '').toLowerCase();
    return nav.startsWith('en-us') ? 'en-US' : 'en-IN';
  };

  let locale = detectLocale();
  const fmt = (n) => Number(n).toLocaleString(locale);

  const nAppeared = scarcity.n_appeared || 2333162;
  const seats = scarcity.total_mbbs_seats || 129602;
  const govtSeats = scarcity.govt_seats || 63859;
  const privateSeats = scarcity.private_seats || 65743;
  const perSeat = scarcity.appeared_per_seat || nAppeared / seats;
  const qualifiedPerSeat = scarcity.qualified_per_seat || 10.153;
  const bandFallback = 10852;
  const bands = razor.near_threshold_bands || razor.near_cutoff_bands || [];
  const oneQ = bands.find(b => Number(b.questions) === 1);
  const nearOne = Number(oneQ?.n_candidates || bandFallback);

  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  };

  const paintNumbers = () => {
    const seatsRounded = Math.round(seats / 1000) * 1000;
    const govtRounded = Math.round(govtSeats / 1000) * 1000;
    const nearRounded = Math.round(nearOne / 1000) * 1000;
    setText('n-appeared', `${(nAppeared / 1e6).toFixed(2)} million`);
    setText('stat-appeared', `${(nAppeared / 1e6).toFixed(2)} million`);
    setText('n-seats', `≈${fmt(seatsRounded)}`);
    setText('stat-seats', `≈${fmt(seatsRounded)}`);
    setText('stat-govt', `≈${fmt(govtRounded)}`);
    setText('per-seat', String(Math.round(perSeat)));
    setText('per-seat-copy', String(Math.round(perSeat)));
    setText('qual-per-100', String(Math.round(100 / qualifiedPerSeat)));
    setText('n-govt', fmt(govtSeats));
    setText('n-private', fmt(privateSeats));
    setText('band-1', `≈${fmt(nearRounded)}`);
  };

  const applyLocale = (next) => {
    locale = next;
    document.documentElement.lang = next;
    try { localStorage.setItem(LOCALE_KEY, next); } catch (_) { /* ignore */ }

    const dict = DICT[next] || DICT['en-IN'];
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (dict[key]) el.textContent = dict[key];
    });
    document.querySelectorAll('[data-i18n-money]').forEach(el => {
      const amount = el.getAttribute('data-i18n-money');
      if (dict.money?.[amount]) el.textContent = dict.money[amount];
    });
    document.querySelectorAll('.locale-btn').forEach(btn => {
      const active = btn.dataset.locale === next;
      btn.classList.toggle('is-active', active);
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
    paintNumbers();

    try {
      const url = new URL(window.location.href);
      url.searchParams.set('lang', next);
      window.history.replaceState({}, '', url);
    } catch (_) { /* file:// or opaque origins */ }
  };

  document.querySelectorAll('.locale-btn').forEach(btn => {
    btn.addEventListener('click', () => applyLocale(btn.dataset.locale));
  });
  applyLocale(locale);

  const readBar = document.getElementById('read-bar');
  const updateReadProgress = () => {
    if (!readBar) return;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const pct = max > 0 ? Math.min(100, (window.scrollY / max) * 100) : 0;
    readBar.style.width = `${pct}%`;
  };
  updateReadProgress();
  window.addEventListener('scroll', updateReadProgress, {passive: true});
  window.addEventListener('resize', updateReadProgress);

  const navContents = document.querySelector('.nav-contents');
  if (navContents) {
    navContents.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => { navContents.open = false; });
    });
  }

  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => { if (entry.isIntersecting) entry.target.classList.add('in'); });
  }, { threshold: .14 });
  document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

  const crowdGrid = document.getElementById('crowd-grid');
  const crowdCaption = document.getElementById('crowd-caption');
  if (crowdGrid && crowdCaption) {
    const crowdN = Math.max(1, Math.round(perSeat));
    const people = Array.from({length:crowdN}, () => {
      const el = document.createElement('span');
      el.className = 'person';
      crowdGrid.appendChild(el);
      return el;
    });
    const crowdObserver = new IntersectionObserver(entries => {
      if (!entries.some(e => e.isIntersecting) || crowdGrid.dataset.played) return;
      crowdGrid.dataset.played = '1';
      const nQualified = Math.min(crowdN, Math.round(crowdN * (scarcity.qualify_rate || .564)));
      setTimeout(() => {
        people.forEach((p,i) => p.classList.add(i < nQualified ? 'qualified' : 'lost'));
        crowdCaption.textContent = `${nQualified} of these ${crowdN} may “qualify.” Still one chair.`;
      }, 450);
      setTimeout(() => {
        if (people[0]) people[0].classList.add('seated');
        crowdCaption.textContent = 'One seat. The rest remain standing—by design.';
      }, 1550);
    }, {threshold:.4});
    const crowdStage = document.getElementById('crowd-stage');
    if (crowdStage) crowdObserver.observe(crowdStage);
  }

  const EXPLANATION_HTML = '<p><strong>Correct answer: A.</strong> EcoRI recognizes GAATTC when read in the 5′→3′ direction. Option C presents a different 5′→3′ sequence; option D is the recognition site for another enzyme, BamHI.</p><p class="diagnostic">It tests a real biology fact. It does not test clinical judgment, communication, or care.</p>';

  const setupStaticQuestionFallback = () => {
    const optionButtons = [...document.querySelectorAll('#question .option')];
    const correctOption = 'A';
    const result = document.getElementById('guess-result');
    const explanation = document.getElementById('question-explanation');
    const blindGuess = document.getElementById('blind-guess');
    const leaveBlank = document.getElementById('leave-blank');
    if (!optionButtons.length || !result || !blindGuess || !leaveBlank) {
      throw new Error('Static question shell is incomplete.');
    }
    if (explanation) explanation.innerHTML = EXPLANATION_HTML;

    let questionResolved = false;
    const resolveQuestion = (choice, mode = 'chosen') => {
      if (questionResolved) return;
      questionResolved = true;
      optionButtons.forEach(button => {
        button.disabled = true;
        if (button.dataset.option === correctOption) button.classList.add('correct');
      });
      blindGuess.disabled = true;
      leaveBlank.disabled = true;

      if (choice == null) {
        result.innerHTML = '<strong>Blank: 0 marks.</strong> A candidate choosing A earns +4, a four-mark gap on this item.';
      } else {
        const selected = optionButtons.find(button => button.dataset.option === choice);
        if (choice !== correctOption) selected?.classList.add('wrong');
        if (choice === correctOption) {
          result.innerHTML = mode === 'random'
            ? '<strong>The blind guess landed on A: +4 marks.</strong> A blind wrong guess would score −1—a five-mark gap.'
            : '<strong>A is correct: +4 marks.</strong> A candidate choosing a wrong option scores −1—a five-mark gap.';
        } else {
          result.innerHTML = mode === 'random'
            ? `<strong>The blind guess landed on ${choice}: −1 mark.</strong> The lucky candidate guessing A finishes five marks ahead on this item.`
            : `<strong>${choice} is wrong: −1 mark.</strong> A candidate choosing A finishes five marks ahead on this item.`;
        }
      }
      if (explanation) explanation.hidden = false;
    };

    optionButtons.forEach(button => button.addEventListener('click', () => resolveQuestion(button.dataset.option)));
    blindGuess.addEventListener('click', () => {
      const choices = ['A', 'B', 'C', 'D'];
      resolveQuestion(choices[Math.floor(Math.random() * choices.length)], 'random');
    });
    leaveBlank.addEventListener('click', () => resolveQuestion(null, 'blank'));
  };

  const injectQuestionBankStyles = () => {
    if (document.querySelector('link[data-question-bank-styles]')) return;
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'question-bank.css';
    link.dataset.questionBankStyles = '1';
    document.head.appendChild(link);
  };

  const setupQuestionBank = (payload) => {
    const questions = Array.isArray(payload?.questions) ? payload.questions : [];
    if (!questions.length) throw new Error('Question bank is empty.');

    injectQuestionBankStyles();
    const card = document.querySelector('.guess-question');
    const marginGrid = card?.querySelector('.margin-grid');
    if (!card || !marginGrid) throw new Error('Question card shell is missing.');

    [...card.children].forEach(child => { if (child !== marginGrid) child.remove(); });
    card.classList.add('qb-loaded');

    const featured = questions.find(q => q.featured) || questions.find(q => q.question_number === 21) || questions[0];
    const letters = ['A', 'B', 'C', 'D'];

    const stage = document.createElement('div');
    stage.className = 'qb-stage';
    card.insertBefore(stage, marginGrid);

    const q = featured;
    let resolved = false;

    const meta = document.createElement('div');
    meta.className = 'qb-meta';
    [q.subject, `NEET-UG ${q.year}`, `Booklet ${q.booklet} · Q${q.question_number}`].forEach(text => {
      const chip = document.createElement('span');
      chip.className = 'qb-chip';
      chip.textContent = text;
      meta.appendChild(chip);
    });

    const brief = document.createElement('p');
    brief.className = 'ecori-brief';
    brief.textContent = 'EcoRI is a laboratory enzyme that cuts DNA at one particular six-letter sequence. Do you remember which one?';

    const prompt = document.createElement('h3');
    prompt.className = 'qb-prompt';
    prompt.textContent = q.prompt;

    const instruction = document.createElement('p');
    instruction.className = 'qb-instruction';
    instruction.textContent = 'Choose an answer, ask for a blind guess, or leave it blank.';

    const optionGrid = document.createElement('div');
    optionGrid.className = 'option-grid qb-option-grid';
    optionGrid.setAttribute('role', 'group');
    optionGrid.setAttribute('aria-label', `Answer choices for question ${q.question_number}`);

    const result = document.createElement('div');
    result.className = 'guess-result qb-result';
    result.setAttribute('aria-live', 'polite');
    result.textContent = 'One candidate guesses correctly: +4. Another guesses incorrectly: −1. Same uncertainty. Five marks apart.';

    const explanation = document.createElement('div');
    explanation.className = 'question-explanation';
    explanation.hidden = true;
    explanation.innerHTML = EXPLANATION_HTML;

    const answerLabel = `${letters[q.correct_index]} — ${q.options[q.correct_index].replace(/\n/g, ' / ')}`;
    let buttons = [];
    let blindGuess;
    let leaveBlank;

    const finish = () => {
      resolved = true;
      buttons.forEach((candidate, candidateIndex) => {
        candidate.disabled = true;
        if (candidateIndex === q.correct_index) candidate.classList.add('correct');
      });
      if (blindGuess) blindGuess.disabled = true;
      if (leaveBlank) leaveBlank.disabled = true;
      explanation.hidden = false;
    };

    const chooseIndex = (index, mode = 'chosen') => {
      if (resolved) return;
      finish();
      const won = index === q.correct_index;
      if (!won) buttons[index]?.classList.add('wrong');
      if (mode === 'random') {
        result.innerHTML = won
          ? `<strong>The blind guess landed on ${letters[index]}: +4 marks.</strong> The official answer is ${answerLabel}. A blind wrong guess would score −1—a five-mark gap.`
          : `<strong>The blind guess landed on ${letters[index]}: −1 mark.</strong> The official answer is ${answerLabel}. A candidate who guessed it correctly finishes five marks ahead on this one item.`;
        return;
      }
      result.innerHTML = won
        ? `<strong>${letters[index]} is correct: +4 marks.</strong> The official answer is ${answerLabel}. A wrong guess on the same item scores −1: a five-mark gap.`
        : `<strong>${letters[index]} is wrong: −1 mark.</strong> The official answer is ${answerLabel}. A candidate who guessed it correctly finishes five marks ahead on this one item.`;
    };

    buttons = q.options.map((text, index) => {
      const button = document.createElement('button');
      button.className = 'option qb-option';
      button.type = 'button';
      button.dataset.index = String(index);

      const letter = document.createElement('span');
      letter.className = 'qb-letter';
      letter.textContent = letters[index];

      const optionText = document.createElement('span');
      optionText.className = text.includes('\n') ? 'qb-option-text qb-seq' : 'qb-option-text';
      optionText.textContent = text;

      button.append(letter, optionText);
      button.addEventListener('click', () => chooseIndex(index));
      optionGrid.appendChild(button);
      return button;
    });

    const actions = document.createElement('div');
    actions.className = 'qb-actions';
    const pathActions = document.createElement('div');
    pathActions.className = 'qb-path-actions';

    blindGuess = document.createElement('button');
    blindGuess.className = 'qb-next';
    blindGuess.type = 'button';
    blindGuess.textContent = 'Guess for me';
    blindGuess.addEventListener('click', () => {
      chooseIndex(Math.floor(Math.random() * q.options.length), 'random');
    });

    leaveBlank = document.createElement('button');
    leaveBlank.className = 'qb-next qb-secondary';
    leaveBlank.type = 'button';
    leaveBlank.textContent = 'Leave blank';
    leaveBlank.addEventListener('click', () => {
      if (resolved) return;
      finish();
      result.innerHTML = `<strong>Blank: 0 marks.</strong> The official answer is ${answerLabel}. A candidate choosing it earns +4—a four-mark gap on this item.`;
    });

    pathActions.append(blindGuess, leaveBlank);
    actions.append(pathActions);

    const ev = document.createElement('details');
    ev.className = 'guess-ev';
    const evSummary = document.createElement('summary');
    evSummary.textContent = 'Why guessing can pay';
    const evBody = document.createElement('p');
    evBody.textContent = 'A blind four-option guess has an expected value of +0.25 marks: one-in-four chance of +4, three-in-four chance of −1. Leaving blank scores 0 for sure.';
    ev.append(evSummary, evBody);

    const source = document.createElement('div');
    source.className = 'qb-source';
    const sourceText = document.createElement('span');
    sourceText.textContent = `Official NTA paper · PDF page ${q.source_page} · answer matched to the final E1 key`;
    const sourceLink = document.createElement('a');
    sourceLink.href = payload.source?.question_paper_url || 'https://neet.nta.nic.in/document/english-set-e1-neet-qp-2020/';
    sourceLink.target = '_blank';
    sourceLink.rel = 'noopener noreferrer';
    sourceLink.textContent = 'View original paper ↗';
    source.append(sourceText, sourceLink);

    stage.append(meta, brief, prompt, instruction, optionGrid, result, ev, explanation, actions, source);
  };

  fetch('question-bank.json', {cache: 'no-store'})
    .then(response => {
      if (!response.ok) throw new Error(`Question bank request failed: ${response.status}`);
      return response.json();
    })
    .then(setupQuestionBank)
    .catch(error => {
      console.warn('Question-bank JSON unavailable; using embedded official samples.', error);
      try {
        setupQuestionBank({
          source: {
            question_paper_url: 'https://neet.nta.nic.in/document/english-set-e1-neet-qp-2020/'
          },
          questions: [
            {
              subject: 'Biology',
              year: 2020,
              booklet: 'E1',
              question_number: 21,
              source_page: 4,
              featured: true,
              prompt: 'The specific palindromic sequence which is recognized by EcoRI is:',
              options: [
                '5′ – GAATTC – 3′\n3′ – CTTAAG – 5′',
                '5′ – GGAACC – 3′\n3′ – CCTTGG – 5′',
                '5′ – CTTAAG – 3′\n3′ – GAATTC – 5′',
                '5′ – GGATCC – 3′\n3′ – CCTAGG – 5′'
              ],
              correct_index: 0
            }
          ]
        });
      } catch (fallbackError) {
        console.warn('Using static featured-question fallback.', fallbackError);
        setupStaticQuestionFallback();
      }
    });

  const laundry = document.getElementById('laundry-machine');
  if (laundry) {
    new IntersectionObserver(entries => {
      if (entries.some(e => e.isIntersecting)) setTimeout(() => laundry.classList.add('washed'), 650);
    }, {threshold:.45}).observe(laundry);
  }

  document.querySelectorAll('.track').forEach(track => {
    for (let i=0; i<18; i++) {
      const runner = document.createElement('span');
      runner.className = 'runner';
      track.appendChild(runner);
    }
  });

  const raceStage = document.getElementById('race-stage');
  if (raceStage) {
    const rows = [...raceStage.querySelectorAll('.race-row')];
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const playRace = () => {
      if (raceStage.dataset.played) return;
      raceStage.dataset.played = '1';
      if (reduceMotion) {
        raceStage.classList.add('played');
        return;
      }
      raceStage.classList.add('sequencing');
      rows.forEach((row, index) => {
        setTimeout(() => row.classList.add('is-on'), index * 900);
      });
      setTimeout(() => raceStage.classList.add('played'), rows.length * 900 + 200);
    };
    new IntersectionObserver(entries => {
      if (entries.some(e => e.isIntersecting)) playRace();
    }, {threshold: .4}).observe(raceStage);
  }

  const defaultSeries = [
    {session:'2016–17', repeater_share:.1247},
    {session:'2017–18', repeater_share:.3836},
    {session:'2018–19', repeater_share:.5041},
    {session:'2019–20', repeater_share:.6940},
    {session:'2020–21', repeater_share:.7142}
  ];
  const rows = tn.length ? tn.map(row => ({
    session: String(row.session)
      .replace('2016-2017','2016–17')
      .replace('2017-2018','2017–18')
      .replace('2018-2019','2018–19')
      .replace('2019-2020','2019–20')
      .replace('2020-2021','2020–21'),
    repeater_share: Number(row.repeater_share)
  })) : defaultSeries;
  const years = document.getElementById('years-chart');
  if (years) {
    rows.forEach(row => {
      const el = document.createElement('div');
      el.className = 'year-row reveal';
      const p = (100 * row.repeater_share).toFixed(1);
      el.innerHTML = `<span>${row.session}</span><div class="year-track"><i class="year-fill" style="--w:${p}%"></i></div><span class="year-pct">${p}%</span>`;
      years.appendChild(el);
      revealObserver.observe(el);
    });
  }
})();
