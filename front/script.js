document.addEventListener('DOMContentLoaded', () => {
    const totalQuestions = 50;
    const questionContainer = document.getElementById('quiz-form-modulo1');
    const resultContainer = document.getElementById('result-modulo1');

    fetch('../input/user_requirement.json')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(userRequirement => {
            const examName = userRequirement.exam;
            const jsonFilePath = `../${examName}_output_questions/questions_answer.json`;

            fetch(jsonFilePath)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Loaded questions data:', data);

                    const examParagraph = document.querySelector('p');
                    if (examParagraph) {
                        examParagraph.textContent = `Exam: ${examName}`;
                    } else {
                        console.error('Paragraph for exam info not found.');
                    }

                    const allQuestions = data;
                    const selectedQuestions = selectRandomQuestions(allQuestions, totalQuestions);
                    console.log('Randomly selected questions:', selectedQuestions);

                    displayQuestions(selectedQuestions);

                    document.querySelector('.btn-primary').addEventListener('click', () => {
                        evaluateQuiz(selectedQuestions);
                    });
                })
                .catch(error => console.error('Error loading questions JSON:', error));
        })
        .catch(error => console.error('Error loading user requirement JSON:', error));

        
    function selectRandomQuestions(allQuestions, num) {
        const evaluableQuestions = allQuestions.filter(q => q.choices && q.choices.length > 0);
        const imageOnlyQuestions = allQuestions.filter(q => q.question_image_src && q.question_image_src.length > 0 && (!q.choices || q.choices.length === 0));
        const otherQuestions = allQuestions.filter(q => !q.choices && (!q.question_image_src || q.question_image_src.length === 0));

        const shuffledEvaluable = shuffleArray(evaluableQuestions);
        const shuffledImageOnly = shuffleArray(imageOnlyQuestions);
        const shuffledOther = shuffleArray(otherQuestions);

        const selectedImageOnly = shuffledImageOnly.slice(0, Math.min(10, imageOnlyQuestions.length));
        const remaining = num - selectedImageOnly.length;

        const selectedEvaluable = shuffledEvaluable.slice(0, Math.min(remaining, evaluableQuestions.length));
        const finalRemaining = remaining - selectedEvaluable.length;

        const selectedOther = shuffledOther.slice(0, finalRemaining);

        return [...selectedImageOnly, ...selectedEvaluable, ...selectedOther];
    }

    function shuffleArray(array) {
        return array.sort(() => Math.random() - 0.5);
    }

    function displayQuestions(questions) {
        questionContainer.innerHTML = '';
        questions.forEach((question, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.classList.add('question', 'mb-3');
            questionDiv.innerHTML = `
                <p><strong>${index + 1}. ${question.question_text}</strong></p>
            `;

            if (question.question_image_src && question.question_image_src.length > 0) {
                questionDiv.innerHTML += question.question_image_src.map(img => `<img src="${img}" class="img-fluid" alt="Question ${index + 1}">`).join('');
            }

            if (question.choices && question.choices.length > 0) {
                const hasMultipleCorrectAnswers = question.choices.filter(choice => choice.correct).length > 1;

                question.choices.forEach(choice => {
                    if (hasMultipleCorrectAnswers) {
                        questionDiv.innerHTML += `
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="q${index}" value="${choice.letter}" id="q${index}-${choice.letter}">
                                <label class="form-check-label" for="q${index}-${choice.letter}">${choice.text}</label>
                            </div>
                        `;
                    } else {
                        questionDiv.innerHTML += `
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="q${index}" value="${choice.letter}" id="q${index}-${choice.letter}">
                                <label class="form-check-label" for="q${index}-${choice.letter}">${choice.text}</label>
                            </div>
                        `;
                    }
                });
            } else if (question.question_image_src && question.question_image_src.length > 0) {
                questionDiv.innerHTML += '<p><i>This question contains images for reference only.</i></p>';
            } else {
                questionDiv.innerHTML += '<p><i>This question is not evaluable and lacks additional information.</i></p>';
            }

            if (question.answer_image_src && question.answer_image_src.length > 0) {
                questionDiv.innerHTML += question.answer_image_src.map(img => `<img src="${img}" class="img-fluid" alt="Answer for Question ${index + 1}">`).join('');
            }

            questionContainer.appendChild(questionDiv);
        });
    }

    function evaluateQuiz(questions) {
        let totalCorrectAnswers = 0;
        let totalEvaluable = 0;

        questions.forEach((question, index) => {
            if (question.choices && question.choices.length > 0) {
                totalEvaluable++;
                const questionDiv = document.querySelectorAll('.question')[index];
                const feedback = document.createElement('p');
                feedback.classList.add('feedback');

                const selectedAnswers = Array.from(document.querySelectorAll(`input[name="q${index}"]:checked`)).map(input => input.value);
                const correctAnswers = question.choices.filter(choice => choice.correct).map(choice => choice.letter);

                if (arraysEqual(selectedAnswers, correctAnswers)) {
                    totalCorrectAnswers++;
                    feedback.textContent = 'Correct';
                    feedback.style.color = 'green';
                } else {
                    feedback.textContent = 'Incorrect';
                    feedback.style.color = 'red';
                }

                questionDiv.appendChild(feedback);
            }
        });

        resultContainer.innerHTML = `Correct answers: ${totalCorrectAnswers}/${totalEvaluable}`;
    }

    function arraysEqual(arr1, arr2) {
        return arr1.length === arr2.length && arr1.every(value => arr2.includes(value));
    }
});
