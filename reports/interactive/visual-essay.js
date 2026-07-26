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
      slider.disabled = true; e.currentTarget.disabled = true;
    });

    const crowdGrid = document.getElementById('crowd-grid');
    const crowdCaption = document.getElementById('crowd-caption');
    const crowdN = Math.max(1, Math.round(perSeat));
    const people = Array.from({length:crowdN}, () => {
      const el = document.createElement('span'); el.className = 'person'; crowdGrid.appendChild(el); return el;
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

    const localQuestionFallback = {
      source: {
        question_paper_url: 'https://cdnbbsr.s3waas.gov.in/s37bc1ec1d9c3426357e69acd5bf320061/uploads/2022/02/2022021555.pdf'
      },
      questions: [
        {subject:'Chemistry', year:2020, booklet:'E1', question_number:91, source_page:11, featured:true, prompt:'Identify a molecule which does not exist.', options:['He₂','Li₂','C₂','O₂'], correct_index:0},
        {subject:'Biology', year:2020, booklet:'E1', question_number:1, source_page:2, prompt:'Which of the following is not an attribute of a population?', options:['Sex ratio','Natality','Mortality','Species interaction'], correct_index:3},
        {subject:'Physics', year:2020, booklet:'E1', question_number:145, source_page:18, prompt:'The phase difference between displacement and acceleration of a particle in simple harmonic motion is:', options:['π rad','3π/2 rad','π/2 rad','Zero'], correct_index:0}
      ]
    };

    const setupFallbackQuestion = () => {
      const options = [...document.querySelectorAll('.option')];
      const correct = options[Math.floor(Math.random() * options.length)]?.dataset.option || 'C';
      options.forEach(button => button.addEventListener('click', () => {
        options.forEach(b => {
          b.disabled = true;
          if (b.dataset.option === correct) b.classList.add('correct');
        });
        const won = button.dataset.option === correct;
        if (!won) button.classList.add('wrong');
        document.getElementById('guess-result').innerHTML = won
          ? `<strong>You guessed correctly: +4 marks.</strong> Another candidate making a wrong guess can finish five marks behind on this one item.`
          : `<strong>You guessed wrong: −1 mark.</strong> Another candidate making the lucky guess can finish five marks ahead on this one item.`;
      }, {once:true}));
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

      const featured = questions.findIndex(q => q.featured);
      const ordered = featured > 0
        ? [questions[featured], ...questions.slice(0, featured), ...questions.slice(featured + 1)]
        : questions.slice();
      const letters = ['A', 'B', 'C', 'D'];
      let currentIndex = 0;

      const stage = document.createElement('div');
      stage.className = 'qb-stage';
      card.insertBefore(stage, marginGrid);

      const renderQuestion = () => {
        const q = ordered[currentIndex];
        stage.replaceChildren();

        const meta = document.createElement('div');
        meta.className = 'qb-meta';
        [q.subject, `NEET-UG ${q.year}`, `Booklet ${q.booklet} · Q${q.question_number}`].forEach(text => {
          const chip = document.createElement('span');
          chip.className = 'qb-chip';
          chip.textContent = text;
          meta.appendChild(chip);
        });

        const prompt = document.createElement('h3');
        prompt.className = 'qb-prompt';
        prompt.textContent = q.prompt;

        const instruction = document.createElement('p');
        instruction.className = 'qb-instruction';
        instruction.textContent = 'Pretend you do not know. Pick one answer and see how a single item creates a five-mark wrong-to-right swing.';

        const optionGrid = document.createElement('div');
        optionGrid.className = 'option-grid qb-option-grid';
        optionGrid.setAttribute('role', 'group');
        optionGrid.setAttribute('aria-label', `Answer choices for question ${q.question_number}`);

        const result = document.createElement('div');
        result.className = 'guess-result qb-result';
        result.setAttribute('aria-live', 'polite');
        result.textContent = 'One option is correct. A blind guess has a 25% chance of +4 and a 75% chance of −1—an expected value of +0.25 marks.';

        const buttons = q.options.map((text, index) => {
          const button = document.createElement('button');
          button.className = 'option qb-option';
          button.type = 'button';
          button.dataset.index = String(index);

          const letter = document.createElement('span');
          letter.className = 'qb-letter';
          letter.textContent = letters[index];

          const optionText = document.createElement('span');
          optionText.textContent = text;

          button.append(letter, optionText);
          button.addEventListener('click', () => {
            buttons.forEach((candidate, candidateIndex) => {
              candidate.disabled = true;
              if (candidateIndex === q.correct_index) candidate.classList.add('correct');
            });
            const won = index === q.correct_index;
            if (!won) button.classList.add('wrong');
            const answer = `${letters[q.correct_index]} — ${q.options[q.correct_index]}`;
            result.innerHTML = won
              ? `<strong>You guessed correctly: +4 marks.</strong> The official answer is ${answer}. A wrong guess on the same item scores −1: a five-mark gap.`
              : `<strong>You guessed wrong: −1 mark.</strong> The official answer is ${answer}. A candidate who guessed it correctly finishes five marks ahead on this one item.`;
          }, {once:true});

          optionGrid.appendChild(button);
          return button;
        });

        const actions = document.createElement('div');
        actions.className = 'qb-actions';
        const next = document.createElement('button');
        next.className = 'qb-next';
        next.type = 'button';
        next.textContent = 'Another official question';
        next.addEventListener('click', () => {
          currentIndex = (currentIndex + 1) % ordered.length;
          renderQuestion();
        });
        const counter = document.createElement('span');
        counter.className = 'qb-counter';
        counter.textContent = `${currentIndex + 1} of ${ordered.length} curated questions`;
        actions.append(next, counter);

        const source = document.createElement('div');
        source.className = 'qb-source';
        const sourceText = document.createElement('span');
        sourceText.textContent = `Official NTA paper · PDF page ${q.source_page} · answer matched to the final E1 key`;
        const sourceLink = document.createElement('a');
        sourceLink.href = payload.source?.question_paper_url || '#';
        sourceLink.target = '_blank';
        sourceLink.rel = 'noopener noreferrer';
        sourceLink.textContent = 'View original paper ↗';
        source.append(sourceText, sourceLink);

        stage.append(meta, prompt, instruction, optionGrid, result, actions, source);
      };

      renderQuestion();
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
          setupQuestionBank(localQuestionFallback);
        } catch (fallbackError) {
          console.warn('Using abstract question fallback.', fallbackError);
          setupFallbackQuestion();
        }
      });

    const laundry = document.getElementById('laundry-machine');
    new IntersectionObserver(entries => {
      if (entries.some(e => e.isIntersecting)) setTimeout(() => laundry.classList.add('washed'), 650);
    }, {threshold:.45}).observe(laundry);

    document.querySelectorAll('.track').forEach(track => {
      for (let i=0; i<18; i++) { const r = document.createElement('span'); r.className = 'runner'; track.appendChild(r); }
    });

    const defaultSeries = [
      {session:'2016–17', repeater_share:.1247},
      {session:'2017–18', repeater_share:.3836},
      {session:'2018–19', repeater_share:.5041},
      {session:'2019–20', repeater_share:.6940},
      {session:'2020–21', repeater_share:.7142}
    ];
    const rows = tn.length ? tn.map(r => ({
      session: String(r.session).replace('2016-2017','2016–17').replace('2017-2018','2017–18').replace('2018-2019','2018–19').replace('2019-2020','2019–20').replace('2020-2021','2020–21'),
      repeater_share: Number(r.repeater_share)
    })) : defaultSeries;
    const years = document.getElementById('years-chart');
    rows.forEach(row => {
      const el = document.createElement('div'); el.className = 'year-row reveal';
      const p = (100 * row.repeater_share).toFixed(1);
      el.innerHTML = `<span>${row.session}</span><div class="year-track"><i class="year-fill" style="--w:${p}%"></i></div><span class="year-pct">${p}%</span>`;
      years.appendChild(el); revealObserver.observe(el);
    });
  })();
