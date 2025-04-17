document.addEventListener('DOMContentLoaded', function () {
    const formsetPrefix = "athlete";
    const minParticipants = window.MIN_PARTICIPANTS || 1;
    let formCount = parseInt(window.FORM_COUNT || "1");
    const availableRoles = window.availableRoles || [];

    function bindPackageCards(container) {
        const packageCards = container.querySelectorAll('.package-card');
        const hiddenSelect = container.querySelector('select[name$="-package"]');
        const optionsContainer = container.querySelector('.package-options-container');
        const index = container.getAttribute('data-index');

        // 📦 Bind click behavior for each package card
        packageCards.forEach(card => {
            const packageId = card.getAttribute('data-package-id');
            card.addEventListener('click', () => {
                // Visual selection
                packageCards.forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                hiddenSelect.value = packageId;

                // Clear existing options
                optionsContainer.innerHTML = '';

                // Load package options via AJAX
                fetch(`/ajax/race/package/${packageId}/options/`)
                    .then(res => res.json())
                    .then(data => {
                        data.package_options.forEach(option => {
                            const label = document.createElement('label');
                            label.textContent = option.name;
                            label.classList.add('form-label');

                            const select = document.createElement('select');
                            select.name = `athlete-${index}-option-${option.id}`;
                            select.classList.add('form-select', 'mb-2');

                            const defaultOpt = document.createElement('option');
                            defaultOpt.disabled = true;
                            defaultOpt.selected = true;
                            defaultOpt.textContent = "Select an option";
                            select.appendChild(defaultOpt);

                            option.options_json.forEach(opt => {
                                const o = document.createElement('option');
                                o.value = opt;
                                o.textContent = opt;
                                select.appendChild(o);
                            });

                            const hiddenInput = document.createElement('input');
                            hiddenInput.type = 'hidden';
                            hiddenInput.name = `athlete-${index}-option-${option.id}-name`;
                            hiddenInput.value = option.name;

                            optionsContainer.appendChild(label);
                            optionsContainer.appendChild(select);
                            optionsContainer.appendChild(hiddenInput);
                        });
                    });
            });
        });

        // ✅ Auto-select if there's only one package
        if (!hiddenSelect.value && packageCards.length === 1) {
            const auto = packageCards[0];
            const packageId = auto.getAttribute('data-package-id');
            hiddenSelect.value = packageId;
            auto.classList.add('selected');
            auto.click();  // Triggers option loading
        }

        // ✅ Re-select if a value is already set (e.g., prefilled form)
        const selectedPackageId = hiddenSelect.value;
        const selectedCard = container.querySelector(`.package-card[data-package-id="${selectedPackageId}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
            selectedCard.click();
        }
    }

    function addForm() {
        const existingForm = document.querySelector('.athlete-form-card');
        const minGroupSize = minParticipants;

        for (let i = 0; i < minGroupSize; i++) {
            const newFormPrefix = formCount;
            const newForm = existingForm.cloneNode(true);

            // 🔁 Replace all index-based IDs, names, labels
            newForm.innerHTML = newForm.innerHTML
                .replaceAll(new RegExp(formsetPrefix + '-(\\d+)-', 'g'), `${formsetPrefix}-${newFormPrefix}-`)
                .replaceAll(new RegExp('id_' + formsetPrefix + '-(\\d+)-', 'g'), `id_${formsetPrefix}-${newFormPrefix}-`)
                .replaceAll(new RegExp('for="' + formsetPrefix + '-(\\d+)-', 'g'), `for="${formsetPrefix}-${newFormPrefix}-`);

            newForm.setAttribute('data-index', newFormPrefix);

            // 🧹 Clear values and errors
            newForm.querySelectorAll('input, select, textarea').forEach(input => {
                if (!['hidden', 'csrfmiddlewaretoken'].includes(input.type)) {
                    input.value = '';
                    if (input.type === 'checkbox') input.checked = false;
                }
            });

            newForm.querySelectorAll('.is-invalid').forEach(input => input.classList.remove('is-invalid'));
            newForm.classList.remove('border-danger');
            newForm.querySelectorAll('.invalid-feedback, .errorlist').forEach(el => el.remove());

            // 🗑️ Remove or re-enable remove button
            const removeBtn = newForm.querySelector('.remove-athlete');
            if (removeBtn) {
                if (minParticipants === 1) {
                    removeBtn.style.display = 'inline-block';
                } else {
                    removeBtn.remove();
                }
            }

            // 🧠 Update header text
            const header = newForm.querySelector('.card-header h5');
            if (header) {
                const icon = header.querySelector('i');
                header.innerHTML = '';
                if (icon) header.appendChild(icon);
                header.append(` Athlete ${formCount + 1}`);
            }

            // 🔁 Append to DOM
            document.getElementById('athleteForms').appendChild(newForm);
            newForm.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // ✅ Bind package cards and auto-select if only one
            bindPackageCards(newForm);

            // ✅ Assign role if defined in global availableRoles
            const roleSelect = newForm.querySelector('select[name$="-role"]');
            if (typeof availableRoles !== "undefined" && Array.isArray(availableRoles) && availableRoles.length > 0 && roleSelect) {
                const assignedRole = availableRoles[newFormPrefix % availableRoles.length];

                // If editable: select it
                if (!roleSelect.disabled) {
                    roleSelect.value = assignedRole.id.toString();
                } else {
                    // Rebuild a locked version of the select
                    roleSelect.innerHTML = "";

                    const opt = document.createElement("option");
                    opt.value = assignedRole.id;
                    opt.textContent = assignedRole.name;
                    opt.selected = true;

                    roleSelect.appendChild(opt);
                    roleSelect.setAttribute("disabled", true);
                    roleSelect.setAttribute("readonly", true);
                }
            }

            formCount++;
        }

        // 🧮 Update TOTAL_FORMS
        document.getElementById(`id_${formsetPrefix}-TOTAL_FORMS`).value = formCount;

        bindRemoveButtons();

        // 👥 Show "remove group" if enough forms exist
        const removeGroupBtn = document.getElementById("removeGroup");
        if (removeGroupBtn && formCount > minParticipants) {
            const wrapper = document.getElementById("removeGroupWrapper");
            if (wrapper) {
                bootstrap.Collapse.getOrCreateInstance(wrapper).show();
            }
        }
    }

    function removeGroup() {
        const groupSize = minParticipants;
        const allCards = document.querySelectorAll('.athlete-form-card');

        if (allCards.length <= groupSize) {
            const alert = document.getElementById("minParticipantAlert");
            const alertText = document.getElementById("minParticipantAlertText");
            alertText.textContent = `This race requires at least ${groupSize} participant(s).`;
            alert.classList.remove("d-none");
            setTimeout(() => alert.classList.add("d-none"), 4000);
            return;
        }

        // 🧹 Remove the last full group
        for (let i = 0; i < groupSize; i++) {
            const lastCard = document.querySelector('.athlete-form-card:last-of-type');
            if (lastCard) lastCard.remove();
        }

        // 🧠 Re-index forms and update total count
        const remainingCards = document.querySelectorAll('.athlete-form-card');
        remainingCards.forEach((cardEl, newIndex) => {
            cardEl.setAttribute('data-index', newIndex);

            const header = cardEl.querySelector('.card-header h5');
            if (header) {
                const icon = header.querySelector('i');
                header.innerHTML = '';
                if (icon) header.appendChild(icon);
                header.append(` Athlete ${newIndex + 1}`);
            }

            cardEl.querySelectorAll('[name], [id], label[for]').forEach(el => {
                ['name', 'id', 'for'].forEach(attr => {
                    const val = el.getAttribute(attr);
                    if (val && val.includes(`${formsetPrefix}-`)) {
                        const updated = val.replace(new RegExp(`${formsetPrefix}-\\d+-`, 'g'), `${formsetPrefix}-${newIndex}-`);
                        el.setAttribute(attr, updated);
                    }
                });
            });
        });

        formCount = remainingCards.length;
        document.getElementById(`id_${formsetPrefix}-TOTAL_FORMS`).value = formCount;

        // ✅ Hide removeGroup if we're back to base
        const wrapper = document.getElementById("removeGroupWrapper");
        if (wrapper && formCount <= minParticipants) {
            bootstrap.Collapse.getOrCreateInstance(wrapper).hide();
        }
    }

    function bindRemoveButtons() {
        document.querySelectorAll('.remove-athlete').forEach(button => {
            button.onclick = function () {
                const card = this.closest('.athlete-form-card');
                const allCards = document.querySelectorAll('.athlete-form-card');

                if (allCards.length <= minParticipants) {
                    const alert = document.getElementById("minParticipantAlert");
                    const alertText = document.getElementById("minParticipantAlertText");
                    alertText.textContent = `This race requires at least ${minParticipants} participant(s). You can't remove more.`;
                    alert.classList.remove("d-none");
                    setTimeout(() => alert.classList.add("d-none"), 4000);
                    return;
                }

                card.remove();

                const remainingCards = document.querySelectorAll('.athlete-form-card');
                remainingCards.forEach((cardEl, newIndex) => {
                    cardEl.setAttribute('data-index', newIndex);

                    const header = cardEl.querySelector('.card-header h5');
                    if (header) {
                        const icon = header.querySelector('i');
                        header.innerHTML = '';
                        if (icon) header.appendChild(icon);
                        header.append(` Athlete ${newIndex + 1}`);
                    }

                    cardEl.querySelectorAll('[name], [id], label[for]').forEach(el => {
                        ['name', 'id', 'for'].forEach(attr => {
                            const val = el.getAttribute(attr);
                            if (val && val.includes(`${formsetPrefix}-`)) {
                                const updated = val.replace(new RegExp(`${formsetPrefix}-\\d+-`, 'g'), `${formsetPrefix}-${newIndex}-`);
                                el.setAttribute(attr, updated);
                            }
                        });
                    });
                });

                formCount = remainingCards.length;
                document.getElementById(`id_${formsetPrefix}-TOTAL_FORMS`).value = formCount;
            };
        });
    }

    document.querySelectorAll('.athlete-form-card').forEach(bindPackageCards);
    bindRemoveButtons();
    document.getElementById('addAthlete').addEventListener('click', addForm);
    const removeGroupBtn = document.getElementById("removeGroup");
    if (removeGroupBtn) {
        removeGroupBtn.addEventListener("click", removeGroup);
    }
});