(() => {
  const D = window.STORY_DATA || {};
  const scarcity = D.scarcity || {};
  const razor = D.razor || {};
  const tn = D.tn_repeater_time_series || D.ticket_cost?.admitted_composition?.post_neet_years || [];
  const fmt = (n) => Number(n).toLocaleString('en-IN');

  const nAppeared = scarcity.n_appeared || 2333162;
  const seats = scarcity.total_mbbs_seats || 129602;
  const perSeat = scarcity.appeared_per_seat || nAppeared / seats;
  const qualifiedPerSeat = scarcity.qualified_per_seat || 10.153;
  document.getElementById('n-appeared').textContent = `${(nAppeared / 1e6).toFixed(2)} million`;
  document.getElementById('n-seats').textContent = fmt(seats);
  document.getElementById('per-seat').textContent = Math.round(perSeat);
  document.getElementById('qual-per-100').textContent = Math.round(100 / qualifiedPerSeat);

  const bandFallback = {1:10852, 5:51292, 10:99876};
  const bands = razor.near_threshold_bands || razor.near_cutoff_bands || [];
  const bandMap = Object.fromEntries(bands.map(b => [Number(b.questions), Number(b.n_candidates)]));
  [1,5,10].forEach(q => document.getElementById(`band-${q}`).textContent = fmt(bandMap[q] || bandFallback[q]));

  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => { if (entry.isIntersecting) entry.target.classList.add('in'); });
  }, { threshold: .14 });
  document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

  const slider = document.getElementById('guess-slider');
  slider.addEventListener('input', () => document.getElementById('guess-num').textContent = slider.value);
  document.getElementById('guess-btn').addEventListener('click', e => {
    document.getElementById('guess-yours').textContent = slider.value;
    document.getElementById('guess-answer').classList.add('show');
    slider.disabled = true;
    e.currentTarget.disabled = true;
  });

  const crowdGrid = document.getElementById('crowd-grid');
  const crowdCaption = document.getElementById('crowd-caption');
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
  crowdObserver.observe(document.getElementById('crowd-stage'));

  const optionButtons = [...document.querySelectorAll('#question .option')];
  const correctOption = 'C';
  const result = document.getElementById('guess-result');
  const explanation = document.getElementById('question-explanation');
  const blindGuess = document.getElementById('blind-guess');
  const leaveBlank = document.getElementById('leave-blank');
  let questionResolved = false;

  function resolveQuestion(choice, mode = 'chosen') {
    if (questionResolved) return;
    questionResolved = true;
    optionButtons.forEach(button => {
      button.disabled = true;
      if (button.dataset.option === correctOption) button.classList.add('correct');
    });
    blindGuess.disabled = true;
    leaveBlank.disabled = true;

    if (choice == null) {
      result.innerHTML = '<strong>Blank: 0 marks.</strong> A candidate choosing C earns +4, a four-mark gap on this item.';
    } else {
      const selected = optionButtons.find(button => button.dataset.option === choice);
      if (choice !== correctOption) selected?.classList.add('wrong');
      if (choice === correctOption) {
        result.innerHTML = mode === 'random'
          ? '<strong>The blind guess landed on C: +4 marks.</strong> A blind wrong guess would score −1—a five-mark gap.'
          : '<strong>C is correct: +4 marks.</strong> A candidate choosing a wrong option scores −1—a five-mark gap.';
      } else {
        result.innerHTML = mode === 'random'
          ? `<strong>The blind guess landed on ${choice}: −1 mark.</strong> The lucky candidate guessing C finishes five marks ahead on this item.`
          : `<strong>${choice} is wrong: −1 mark.</strong> A candidate choosing C finishes five marks ahead on this item.`;
      }
    }
    explanation.hidden = false;
  }

  optionButtons.forEach(button => button.addEventListener('click', () => resolveQuestion(button.dataset.option)));
  blindGuess.addEventListener('click', () => {
    const choices = ['A','B','C','D'];
    resolveQuestion(choices[Math.floor(Math.random() * choices.length)], 'random');
  });
  leaveBlank.addEventListener('click', () => resolveQuestion(null, 'blank'));

  const laundry = document.getElementById('laundry-machine');
  new IntersectionObserver(entries => {
    if (entries.some(e => e.isIntersecting)) setTimeout(() => laundry.classList.add('washed'), 650);
  }, {threshold:.45}).observe(laundry);

  document.querySelectorAll('.track').forEach(track => {
    for (let i=0; i<18; i++) {
      const runner = document.createElement('span');
      runner.className = 'runner';
      track.appendChild(runner);
    }
  });

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
  rows.forEach(row => {
    const el = document.createElement('div');
    el.className = 'year-row reveal';
    const p = (100 * row.repeater_share).toFixed(1);
    el.innerHTML = `<span>${row.session}</span><div class="year-track"><i class="year-fill" style="--w:${p}%"></i></div><span class="year-pct">${p}%</span>`;
    years.appendChild(el);
    revealObserver.observe(el);
  });
})();
