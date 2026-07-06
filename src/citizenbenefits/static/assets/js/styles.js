(function () {
    let currentLang = 'en';
    let lastResults = null; // Stores { type: 'results'|'summary', data: [...] }
    const translations = {};

    const countryPrograms = {
        CA: {
            en: "programs like the Canada Child Benefit, GST/HST Credit, Employment Insurance, and the Canada Workers Benefit",
            es: "programas como el Beneficio Infantil de Canada, el Credito GST/HST, el Seguro de Desempleo y el Beneficio para Trabajadores de Canada",
            fr: "des programmes comme l'Allocation canadienne pour enfants, le credit pour la TPS/TVH, l'assurance-emploi et l'Allocation canadienne pour les travailleurs",
            de: "Programme wie das Canada Child Benefit, das GST/HST Credit, die Arbeitslosenversicherung und das Canada Workers Benefit"
        },
        GB: {
            en: "programs like Universal Credit, Child Benefit, Pension Credit, and Housing Benefit",
            es: "programas como el Credito Universal, el Beneficio por Hijo, el Credito de Pension y el Beneficio de Vivienda",
            fr: "des programmes comme le Credit universel, l'Allocation familiale, le credit de pension et l'Aide au logement",
            de: "Programme wie Universal Credit, Child Benefit, Pension Credit und Housing Benefit"
        },
        AU: {
            en: "Centrelink payments like JobSeeker, Family Tax Benefit, Age Pension, and Rent Assistance",
            es: "pagos de Centrelink como JobSeeker, el Beneficio Fiscal Familiar, la Pension de Vejez y la Asistencia de Alquiler",
            fr: "des paiements de Centrelink comme JobSeeker, l'Allocation familiale, la pension de retraite et l'aide au loyer",
            de: "Centrelink-Zahlungen wie JobSeeker, Family Tax Benefit, Altersrente und Rentenbeihilfe"
        },
        DE: {
            en: "programs like Grundsicherungsgeld (formerly Buergergeld), Kindergeld, Wohngeld, and Elterngeld",
            es: "programas como Grundsicherungsgeld (anteriormente Buergergeld), Kindergeld, Wohngeld y Elterngeld",
            fr: "des programmes comme la Grundsicherungsgeld (anciennement Buergergeld), le Kindergeld, le Wohngeld et l'Elterngeld",
            de: "Programme wie Grundsicherungsgeld (ehemals Buergergeld), Kindergeld, Wohngeld und Einleitung"
        },
        FR: {
            en: "programs like RSA, CAF housing assistance, and Prime d'Activite",
            es: "programas como RSA, asistencia de vivienda CAF y Prime d'Activite",
            fr: "des programmes comme le RSA, les aides au logement de la CAF et la Prime d'activite",
            de: "Programme wie RSA, CAF-Wohnbeihilfe und Prime d'Activite"
        },
        ES: {
            en: "programs like Ingreso Minimo Vital and family support benefits",
            es: "programas como el Ingreso Minimo Vital y los beneficios de apoyo familiar",
            fr: "des programmes comme l'Ingreso Minimo Vital et les prestations de soutien familial",
            de: "Programme wie Ingreso Minimo Vital und Unterstuetzung fuer Familien"
        },
        MX: {
            en: "Programas para el Bienestar including pensions and family support",
            es: "Programas para el Bienestar incluyendo pensiones y apoyo familiar",
            fr: "des Programas para el Bienestar, y compris les pensions et le soutien familial",
            de: "Programas para el Bienestar einschliesslich Renten und Familienbeihilfe"
        }
    };

    const countryDefaultLang = {
        US: 'en',
        CA: 'en',
        GB: 'en',
        AU: 'en',
        DE: 'de',
        FR: 'fr',
        ES: 'es',
        MX: 'es'
    };

    document.addEventListener('DOMContentLoaded', () => {
        // DOM Elements
        const countrySelect = document.getElementById('countrySelect');
    const langSelect = document.getElementById('langSelect');
    const intakePanel = document.getElementById('intakePanel');
    const globalPanel = document.getElementById('globalPanel');
    const globalFlag = document.getElementById('globalFlag');
    const targetCountryName = document.getElementById('targetCountryName');
    const resultsPanel = document.getElementById('resultsPanel');
    const errorPanel = document.getElementById('errorPanel');
    const form = document.getElementById('eligibilityForm');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsContainer = document.getElementById('resultsContainer');
    const spinnerTimer = document.getElementById('spinnerTimer');
    const queryTimeDisplay = document.getElementById('queryTimeDisplay');

    // Create and append the dynamic tooltip element to body (prevents parent clipping)
    const tooltipEl = document.createElement('div');
    tooltipEl.id = 'appTooltip';
    tooltipEl.className = 'info-popup hidden';
    tooltipEl.innerHTML = `
        <div class="info-popup-header">
            <span class="info-popup-title" id="tooltipTitle"></span>
        </div>
        <div class="info-popup-body" id="tooltipBody"></div>
    `;
    document.body.appendChild(tooltipEl);

    // Dynamically inject info triggers next to labels
    const fieldsToInject = [
        { id: 'labelState', key: 'state' },
        { id: 'labelZip', key: 'zip' },
        { id: 'labelHouseholdSize', key: 'householdSize' },
        { id: 'labelIncomeBand', key: 'incomeBand' },
        { id: 'labelEarnedIncomeShare', key: 'earnedIncomeShare' },
        { id: 'labelAgeBand', key: 'ageBand' },
        { id: 'labelNumChildren', key: 'numChildren' }
    ];

    fieldsToInject.forEach(field => {
        const label = document.getElementById(field.id);
        if (label && !label.querySelector('.info-trigger')) {
            const trigger = document.createElement('span');
            trigger.className = 'info-trigger';
            trigger.setAttribute('data-tooltip', field.key);
            trigger.innerHTML = `
                <svg class="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <circle cx="12" cy="8" r="1" fill="currentColor"></circle>
                </svg>
            `;
            label.appendChild(trigger);
        }
    });

    // Make the manually placed Citizenship trigger support the same key
    const statusTrigger = document.getElementById('statusTrigger');
    if (statusTrigger) {
        statusTrigger.setAttribute('data-tooltip', 'status');
    }

    const activeTooltip = {
        trigger: null,
        popup: null
    };

    function showTooltip(trigger, key) {
        hideTooltip();

        const trans = translations[currentLang];
        if (!trans) return;

        let title = '';
        let body = '';
        let popup = tooltipEl;

        if (key === 'status') {
            popup = document.getElementById('statusInfoPopup');
            // Safely move status popup to body to avoid parent clipping/position issues
            if (popup && popup.parentElement !== document.body) {
                document.body.appendChild(popup);
            }
            title = trans.statusPopupTitle || '';
            body = trans.statusPopupBody || '';
            
            // Set text inside restored manual popup elements
            const titleEl = document.getElementById('statusPopupTitle');
            const bodyEl = document.getElementById('statusPopupBody');
            if (titleEl) titleEl.textContent = title;
            if (bodyEl) bodyEl.textContent = body;
        } else {
            if (key === 'state') {
                title = trans.labelState || '';
                body = trans.titleStateInput || '';
            } else if (key === 'zip') {
                title = trans.labelZip || '';
                body = trans.titleZipInput || '';
            } else if (key === 'householdSize') {
                title = trans.labelHouseholdSize || '';
                body = trans.titleHouseholdSizeInput || '';
            } else if (key === 'incomeBand') {
                title = trans.labelIncomeBand || '';
                body = trans.titleIncomeBandSelect || '';
            } else if (key === 'earnedIncomeShare') {
                title = trans.labelEarnedIncomeShare || '';
                body = trans.titleEarnedIncomeShareSelect || '';
            } else if (key === 'ageBand') {
                title = trans.labelAgeBand || '';
                body = trans.titleAgeBandSelect || '';
            } else if (key === 'numChildren') {
                title = trans.labelNumChildren || '';
                body = trans.titleNumChildrenSelect || '';
            }
            
            const tooltipTitleEl = document.getElementById('tooltipTitle');
            const tooltipBodyEl = document.getElementById('tooltipBody');
            if (tooltipTitleEl) tooltipTitleEl.textContent = title;
            if (tooltipBodyEl) tooltipBodyEl.textContent = body;
        }

        if (!popup) return;

        popup.className = 'info-popup active';

        // Wait a tick for browser layout update before measuring
        requestAnimationFrame(() => {
            const triggerRect = trigger.getBoundingClientRect();
            const popupRect = popup.getBoundingClientRect();

            // Calculate auto-position (top or bottom based on viewport space)
            let top = triggerRect.top - popupRect.height - 12 + window.scrollY;
            let left = triggerRect.left + (triggerRect.width / 2) - (popupRect.width / 2) + window.scrollX;

            if (triggerRect.top - popupRect.height - 20 < 0) {
                // Not enough room on top, place below
                top = triggerRect.bottom + 12 + window.scrollY;
            }

            // Keep within viewport boundaries
            const maxLeft = window.innerWidth - popupRect.width - 12;
            if (left < 12) {
                left = 12;
            } else if (left > maxLeft) {
                left = maxLeft;
            }

            popup.style.top = `${top}px`;
            popup.style.left = `${left}px`;
            activeTooltip.trigger = trigger;
            activeTooltip.popup = popup;
        });
    }

    function hideTooltip() {
        if (activeTooltip.popup) {
            activeTooltip.popup.className = 'info-popup hidden';
        }
        const statusPopup = document.getElementById('statusInfoPopup');
        if (statusPopup) {
            statusPopup.className = 'info-popup hidden';
        }
        tooltipEl.className = 'info-popup hidden';
        activeTooltip.trigger = null;
        activeTooltip.popup = null;
    }

    // Tooltip event handlers
    document.addEventListener('click', (e) => {
        const trigger = e.target.closest('.info-trigger');
        if (trigger) {
            e.stopPropagation();
            const key = trigger.getAttribute('data-tooltip');
            if (activeTooltip.trigger === trigger) {
                hideTooltip();
            } else {
                showTooltip(trigger, key);
            }
        } else {
            if (activeTooltip.trigger && !tooltipEl.contains(e.target)) {
                const statusPopup = document.getElementById('statusInfoPopup');
                if (!statusPopup || !statusPopup.contains(e.target)) {
                    hideTooltip();
                }
            }
        }
    });

    // Scroll to top and pulse animation on logo click
    const navLogo = document.querySelector('.nav-logo');
    if (navLogo) {
        navLogo.addEventListener('click', (e) => {
            e.preventDefault();
            const wrapper = navLogo.querySelector('.nav-logo-icon-wrapper');
            if (wrapper) {
                wrapper.classList.remove('pulse-animation');
                void wrapper.offsetWidth; // trigger reflow
                wrapper.classList.add('pulse-animation');
                setTimeout(() => {
                    wrapper.classList.remove('pulse-animation');
                }, 600);
            }
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    const footerLogo = document.querySelector('.footer-logo .nav-logo-icon-wrapper');
    if (footerLogo) {
        footerLogo.addEventListener('click', (e) => {
            footerLogo.classList.remove('pulse-animation');
            void footerLogo.offsetWidth; // trigger reflow
            footerLogo.classList.add('pulse-animation');
            setTimeout(() => {
                footerLogo.classList.remove('pulse-animation');
            }, 600);
        });
    }

    // Helper functions to safely update DOM text/placeholder/attributes without crashing
    function safeText(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val || '';
    }
    function safeHtml(id, val) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = val || '';
    }
    function safePlaceholder(id, val) {
        const el = document.getElementById(id);
        if (el) el.placeholder = val || '';
    }
    function safeTitle(id, val) {
        const el = document.getElementById(id);
        if (el) el.title = val || '';
    }
    function safeLabelText(id, val) {
        const el = document.getElementById(id);
        if (el && el.childNodes && el.childNodes.length > 0) {
            el.childNodes[0].textContent = val || '';
        } else if (el) {
            el.textContent = val || '';
        }
    }

    // Frontend translation function for eligibility reason templates
    function translateReason(text, lang) {
        if (!text) return '';
        const trans = translations[lang];
        if (!trans || !trans.reasonTranslations) return text;

        let translated = text;
        trans.reasonTranslations.forEach(item => {
            try {
                const regex = new RegExp(item.pattern, 'g');
                translated = translated.replace(regex, item.replacement);
            } catch (err) {
                console.error("Regex translation error:", err);
            }
        });
        return translated;
    }

    // Dynamic rendering of results so they can be re-translated when the language changes
    function renderResults() {
        if (!resultsContainer || !lastResults) return;
        resultsContainer.innerHTML = '';
        const trans = translations[currentLang] || {};

        if (lastResults.type === 'results') {
            lastResults.data.forEach(program => {
                const statusClass = program.likely_eligible.toLowerCase();
                const card = document.createElement('div');
                card.className = `result-card ${statusClass}`;

                const badgeText = trans['badge_' + program.likely_eligible.toLowerCase()] || program.likely_eligible.toUpperCase().replace(/_/g, ' ');
                const labelSource = trans.labelSource || 'Source';
                const labelPortal = trans.labelOfficialPortal || 'Official State Portal';
                const translatedReason = translateReason(program.reason, currentLang);

                card.innerHTML = `
                    <div class="card-top">
                        <span class="program-name">${program.program.replace('_', '/')}</span>
                        <span class="badge ${statusClass}">${badgeText}</span>
                    </div>
                    <p class="reason-text">${translatedReason}</p>
                    <div class="source-cited">
                        <span>${labelSource}:</span>
                        <a href="${program.source_cited}" target="_blank" class="source-link">${program.source_cited}</a>
                        <span>(${formatLocalDate(program.as_of_date, currentLang, countrySelect ? countrySelect.value : 'US')})</span>
                    </div>
                    ${program.apply_link ? `<a href="${program.apply_link}" target="_blank" class="btn-apply" title="${(translations[currentLang] && translations[currentLang]['titleBtnApply_' + program.program]) || (translations[currentLang] && translations[currentLang].titleBtnApply) || ''}">${labelPortal}</a>` : ''}
                `;
                resultsContainer.appendChild(card);
            });

            if (resultsPanel) {
                resultsPanel.classList.remove('hidden');
            }
        } else if (lastResults.type === 'summary') {
            const statusClass = 'unlikely';
            const card = document.createElement('div');
            card.className = `result-card ${statusClass}`;
            const translatedSummary = translateReason(lastResults.text, currentLang);
            card.innerHTML = `
                <div class="card-top">
                    <span class="program-name">System Notice</span>
                    <span class="badge ${statusClass}">NOTICE</span>
                </div>
                <p class="reason-text">${translatedSummary}</p>
            `;
            resultsContainer.appendChild(card);
            if (resultsPanel) {
                resultsPanel.classList.remove('hidden');
            }
        }
    }

    async function setLanguage(lang) {
        currentLang = lang;
        if (langSelect) langSelect.value = lang;

        if (!translations[lang]) {
            try {
                const res = await fetch(`/static/lang/${lang}.json?v=5.0`);
                if (!res.ok) {
                    throw new Error(`Failed to load translation: ${lang}`);
                }
                translations[lang] = await res.json();
            } catch (err) {
                console.error(err);
                if (lang !== 'en') {
                    await setLanguage('en');
                }
                return;
            }
        }

        const trans = translations[lang] || {};

        if (trans.pageTitle) {
            document.title = trans.pageTitle;
        }
        if (trans.metaDescription) {
            const metaDesc = document.querySelector('meta[name="description"]');
            if (metaDesc) {
                metaDesc.setAttribute('content', trans.metaDescription);
            }
        }

        // Translate texts safely
        safeText('selectLanguageLabel', trans.selectLanguageLabel);
        safeText('introText', trans.introText);
        safeText('selectCountryLabel', trans.selectCountryLabel);
        safeText('globalTitle', trans.globalTitle);
        // safePlaceholder('notifyInput', trans.notifyInputPlaceholder);
        // safeText('btnNotify', trans.btnNotify);
        // safeTitle('btnNotify', trans.btnNotifyTitle);
        safeText('globalComingSoon', trans.globalComingSoon);
        safeText('globalWhyText', trans.globalWhyText);
        safeText('intakeTitle', trans.intakeTitle);
        safeText('intakeSubtitle', trans.intakeSubtitle);
        safeText('intakeBadgeText', trans.intakeBadgeText);
        safeText('navHowItWorks', trans.navHowItWorks);
        safeText('navSupportedPrograms', trans.navSupportedPrograms);
        safeText('navPrivacyPrinciples', trans.navPrivacyPrinciples);

        // Update nav link title attributes
        const link1 = document.getElementById('navHowItWorks');
        if (link1 && trans.titleNavMission) {
            link1.title = trans.titleNavMission;
        }
        const link2 = document.getElementById('navSupportedPrograms');
        if (link2 && trans.titleNavPrograms) {
            link2.title = trans.titleNavPrograms;
        }
        const link3 = document.getElementById('navPrivacyPrinciples');
        if (link3 && trans.titleNavPrivacy) {
            link3.title = trans.titleNavPrivacy;
        }
        const logoLink = document.querySelector('.nav-logo');
        if (logoLink && trans.titleNavLogo) {
            logoLink.title = trans.titleNavLogo;
        }
        safeHtml('heroTitle', trans.heroTitle);
        safeText('featureTitle1', trans.featureTitle1);
        safeText('featureDesc1', trans.featureDesc1);
        safeText('featureTitle2', trans.featureTitle2);
        safeText('featureDesc2', trans.featureDesc2);
        safeText('featureTitle3', trans.featureTitle3);
        safeText('featureDesc3', trans.featureDesc3);
        safeText('featureTitle4', trans.featureTitle4);
        safeText('featureDesc4', trans.featureDesc4);
        safeText('badgeNoSignup', trans.badgeNoSignup);
        safeText('badgeDataPrivacy', trans.badgeDataPrivacy);

        // Form labels and titles safely
        safeLabelText('labelStatus', trans.labelStatus);
        safeLabelText('labelState', trans.labelState);
        safeLabelText('labelZip', trans.labelZip);
        safeLabelText('labelHouseholdSize', trans.labelHouseholdSize);

        const incomeBandLabel = document.getElementById('labelIncomeBand');
        if (incomeBandLabel) {
            if (incomeBandLabel.childNodes && incomeBandLabel.childNodes.length > 0) {
                incomeBandLabel.childNodes[0].textContent = trans.labelIncomeBand || '';
            } else {
                incomeBandLabel.textContent = trans.labelIncomeBand || '';
            }
            incomeBandLabel.title = trans.incomeBandTitle || '';
        }

        const earnedIncomeLabel = document.getElementById('labelEarnedIncomeShare');
        if (earnedIncomeLabel) {
            if (earnedIncomeLabel.childNodes && earnedIncomeLabel.childNodes.length > 0) {
                earnedIncomeLabel.childNodes[0].textContent = trans.labelEarnedIncomeShare || '';
            } else {
                earnedIncomeLabel.textContent = trans.labelEarnedIncomeShare || '';
            }
            earnedIncomeLabel.title = trans.earnedIncomeShareTitle || '';
        }

        safeLabelText('labelAgeBand', trans.labelAgeBand);
        safeLabelText('labelNumChildren', trans.labelNumChildren);
        safeText('labelCircumstances', trans.labelCircumstances);

        safeText('spanDisability', trans.spanDisability);
        safeText('spanPregnant', trans.spanPregnant);
        safeText('spanMarried', trans.spanMarried);
        safeText('spanVeteran', trans.spanVeteran);

        safeText('btnSubmitText', trans.btnSubmitText);
        safeTitle('btnSubmit', trans.btnSubmitTitle);
        safeText('spinnerText', trans.spinnerText);
        safeHtml('formNote', trans.formNote);

        safeText('whyTitle', trans.whyTitle);
        safeText('whyText', trans.whyText);
        safeText('updatedPillText', trans.updatedPillText);
        safeText('whyCardTitle1', trans.whyCardTitle1);
        safeText('whyCardDesc1', trans.whyCardDesc1);
        safeText('whyCardTitle2', trans.whyCardTitle2);
        safeText('whyCardDesc2', trans.whyCardDesc2);
        safeText('whyCardTitle3', trans.whyCardTitle3);
        safeText('whyCardDesc3', trans.whyCardDesc3);
        safeText('programsSectionTitle', trans.programsSectionTitle);
        safeText('programBoxDesc1', trans.programBoxDesc1);
        safeText('programBoxDesc2', trans.programBoxDesc2);
        safeText('programBoxDesc3', trans.programBoxDesc3);
        safeText('programBoxDesc4', trans.programBoxDesc4);
        safeText('programBoxDesc5', trans.programBoxDesc5);
        safeText('resultsHeader', trans.resultsHeader);

        safeText('footerDisclaimer', trans.footerDisclaimer);
        safeHtml('footerCopyright', trans.footerCopyright);
        safeText('footerDesc', trans.footerDesc);
        safeText('footerCopyrightSide', trans.footerCopyright);
        safeText('advisoriesHeader', trans.advisoriesHeader);
        safeText('govAffiliationTitle', trans.govAffiliationTitle);
        safeText('govAffiliationText', trans.govAffiliationText);
        safeText('rulesContingencyTitle', trans.rulesContingencyTitle);
        safeText('rulesContingencyText', trans.rulesContingencyText);

        // Set element title attributes safely
        if (countrySelect) countrySelect.title = trans.titleCountrySelect || '';
        if (langSelect) langSelect.title = trans.titleLangSelect || '';
        safeTitle('status', trans.titleStatusSelect);
        safeTitle('state', trans.hintState);
        safeTitle('zip', trans.hintZip);
        safeTitle('household_size', trans.hintHouseholdSize);
        safeTitle('total_income_band', trans.hintIncomeBand);
        safeTitle('earned_income_share', trans.hintEarnedIncomeShare);
        safeTitle('age_band', trans.hintAgeBand);
        safeTitle('num_children', trans.hintNumChildren);

        const hasDisability = document.getElementById('has_disability');
        if (hasDisability && hasDisability.parentElement) {
            hasDisability.parentElement.title = trans.titleCircumstanceDisability || '';
        }
        const isPregnant = document.getElementById('is_pregnant');
        if (isPregnant && isPregnant.parentElement) {
            isPregnant.parentElement.title = trans.titleCircumstancePregnant || '';
        }
        const isMarried = document.getElementById('is_married');
        if (isMarried && isMarried.parentElement) {
            isMarried.parentElement.title = trans.titleCircumstanceMarried || '';
        }
        const isVeteran = document.getElementById('is_veteran_or_military');
        if (isVeteran && isVeteran.parentElement) {
            isVeteran.parentElement.title = trans.titleCircumstanceVeteran || '';
        }

        // Translate Select Dropdowns safely
        document.querySelectorAll('#status option').forEach(opt => {
            if (opt.value === "") {
                opt.textContent = trans.statusPlaceholder || '';
            } else if (trans.statusOptions && trans.statusOptions[opt.value]) {
                opt.textContent = trans.statusOptions[opt.value];
            }
        });
        document.querySelectorAll('#state option').forEach(opt => {
            if (opt.value === "") {
                opt.textContent = trans.statePlaceholder || '';
            }
        });
        document.querySelectorAll('#total_income_band option').forEach(opt => {
            if (opt.value === "") {
                opt.textContent = trans.incomeBandPlaceholder || '';
            } else if (trans.incomeBandOptions && trans.incomeBandOptions[opt.value]) {
                opt.textContent = trans.incomeBandOptions[opt.value];
            }
        });
        document.querySelectorAll('#earned_income_share option').forEach(opt => {
            if (opt.value === "") {
                opt.textContent = trans.earnedIncomeSharePlaceholder || '';
            } else if (trans.earnedIncomeShareOptions && trans.earnedIncomeShareOptions[opt.value]) {
                opt.textContent = trans.earnedIncomeShareOptions[opt.value];
            }
        });
        document.querySelectorAll('#age_band option').forEach(opt => {
            if (opt.value === "") {
                opt.textContent = trans.ageBandPlaceholder || '';
            } else if (trans.ageBandOptions && trans.ageBandOptions[opt.value]) {
                opt.textContent = trans.ageBandOptions[opt.value];
            }
        });

        // Re-translate results if they are currently displayed
        if (lastResults) {
            renderResults();
        }

        // Refresh global card if currently visible
        updateGlobalCard();
    }

    function updateGlobalCard() {
        if (!countrySelect) return;
        const country = countrySelect.value;
        if (country === 'US') {
            if (intakePanel) intakePanel.classList.remove('hidden');
            if (globalPanel) globalPanel.classList.add('hidden');
        } else {
            if (intakePanel) intakePanel.classList.add('hidden');
            if (globalPanel) globalPanel.classList.remove('hidden');

            const optionText = countrySelect.options[countrySelect.selectedIndex].text;
            const flagMatch = optionText.match(/[\uD83C-\uDBFF\uDC00-\uDFFF]+/);
            const flagEmoji = flagMatch ? flagMatch[0] : '';
            const countryName = optionText.replace(/[\uD83C-\uDBFF\uDC00-\uDFFF]/g, '').trim();

            if (globalFlag) globalFlag.textContent = flagEmoji;
            if (targetCountryName) targetCountryName.textContent = countryName;

            const progText = countryPrograms[country] ? countryPrograms[country][currentLang] : '';

            const globalDesc = document.getElementById('globalDesc');
            if (globalDesc && translations[currentLang]) {
                let descTemplate = translations[currentLang].globalDesc || '';
                descTemplate = descTemplate.replace('{country}', countryName).replace('{programs}', progText);
                globalDesc.textContent = descTemplate;
            }
        }
    }

    function formatLocalDate(dateStr, lang, country) {
        if (!dateStr || !/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
            return dateStr;
        }
        const parts = dateStr.split('-');
        const year = parts[0];
        const month = parts[1];
        const day = parts[2];

        if (lang === 'en' && country === 'US') {
            return `${month}/${day}/${year}`;
        } else if (lang === 'de') {
            return `${day}.${month}.${year}`;
        } else {
            return `${day}/${month}/${year}`;
        }
    }

    // Event Listeners with Null Checks
    if (countrySelect) {
        countrySelect.addEventListener('change', async () => {
            if (resultsPanel) resultsPanel.classList.add('hidden');
            if (errorPanel) errorPanel.classList.add('hidden');
            lastResults = null; // Clear old results when country changes
            const country = countrySelect.value;
            if (countryDefaultLang[country]) {
                await setLanguage(countryDefaultLang[country]);
            } else {
                updateGlobalCard();
            }
        });
    }

    if (langSelect) {
        langSelect.addEventListener('change', (e) => {
            setLanguage(e.target.value);
        });
    }

    // const btnNotify = document.getElementById('btnNotify');
    // if (btnNotify) {
    //     btnNotify.addEventListener('click', () => {
    //         alert('Thank you! You will be notified when support becomes available.');
    //     });
    // }

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (resultsPanel) resultsPanel.classList.add('hidden');
            if (errorPanel) errorPanel.classList.add('hidden');
            if (queryTimeDisplay) {
                queryTimeDisplay.classList.add('hidden');
                queryTimeDisplay.textContent = '';
            }
            if (resultsContainer) resultsContainer.innerHTML = '';
            if (loadingSpinner) {
                loadingSpinner.classList.remove('hidden');
                loadingSpinner.scrollIntoView({ behavior: "smooth" });
            }

            if (spinnerTimer) {
                const trans = translations[currentLang] || {};
                const template = trans.spinnerTimerText || 'Time: {seconds}s';
                spinnerTimer.textContent = template.replace('{seconds}', '0');
            }

            const startTime = performance.now();
            let timerSeconds = 0;
            const timerInterval = setInterval(() => {
                timerSeconds++;
                if (spinnerTimer) {
                    const trans = translations[currentLang] || {};
                    const template = trans.spinnerTimerText || 'Time: {seconds}s';
                    spinnerTimer.textContent = template.replace('{seconds}', timerSeconds);
                }
            }, 1000);

            const requestData = {
                status: document.getElementById('status').value,
                state: document.getElementById('state').value,
                zip: document.getElementById('zip').value,
                household_size: parseInt(document.getElementById('household_size').value || '1'),
                total_income_band: document.getElementById('total_income_band').value,
                earned_income_share: document.getElementById('earned_income_share').value,
                age_band: document.getElementById('age_band').value,
                has_disability: document.getElementById('has_disability').checked,
                is_pregnant: document.getElementById('is_pregnant').checked,
                num_children: parseInt(document.getElementById('num_children').value || '0'),
                is_married: document.getElementById('is_married').checked,
                is_veteran_or_military: document.getElementById('is_veteran_or_military').checked
            };

            try {
                const response = await fetch('/eligibility', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestData)
                });

                const data = await response.json();

                if (!response.ok) {
                    let errMsg = 'An error occurred while calculating eligibility.';
                    if (data && data.detail) {
                        if (Array.isArray(data.detail)) {
                            errMsg = data.detail.map(err => err.msg || JSON.stringify(err)).join(', ');
                        } else if (typeof data.detail === 'string') {
                            errMsg = data.detail;
                        } else {
                            errMsg = JSON.stringify(data.detail);
                        }
                    }
                    throw new Error(errMsg);
                }

                if (data.results && data.results.length > 0) {
                    lastResults = { type: 'results', data: data.results };
                    renderResults();
                    if (resultsPanel) {
                        resultsPanel.scrollIntoView({ behavior: "smooth" });
                    }
                } else if (data.summary) {
                    lastResults = { type: 'summary', text: data.summary };
                    renderResults();
                    if (resultsPanel) {
                        resultsPanel.scrollIntoView({ behavior: "smooth" });
                    }
                } else {
                    throw new Error('No eligibility results returned.');
                }

            } catch (err) {
                if (errorPanel) {
                    errorPanel.textContent = err.message;
                    errorPanel.classList.remove('hidden');
                    errorPanel.scrollIntoView({ behavior: "smooth" });
                }
            } finally {
                clearInterval(timerInterval);
                const elapsedSeconds = Math.round((performance.now() - startTime) / 1000);
                if (loadingSpinner) loadingSpinner.classList.add('hidden');
                
                if (queryTimeDisplay) {
                    const trans = translations[currentLang] || {};
                    const template = trans.queryTimeText || 'Query Time: {seconds}s';
                    queryTimeDisplay.textContent = template.replace('{seconds}', elapsedSeconds);
                    queryTimeDisplay.classList.remove('hidden');
                }
            }
        });
    }

        // Initialize Page
        setLanguage('en');
    });
})();
