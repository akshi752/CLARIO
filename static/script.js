const path = window.location.pathname;

if (path === "/speech") {

    let rawText = "";
    const sessionId = crypto.randomUUID();

    const sentences = [
        "I want to explain my idea clearly and confidently today.",
        "Today I am going to describe my favorite hobby in detail.",
        "Please read this sentence at a steady and comfortable speed.",
        "The students completed their assignments before the deadline.",
        "Sally sees seven shiny seashells by the seashore."
    ];

    let index = 0;
    let recognition;
    let startTime;

    const sentenceEl = document.getElementById("sentence");
    const spokenTextEl = document.getElementById("spokenText");
    const micBtn = document.getElementById("micBtn");
    const seeBtn = document.getElementById("seeResultsBtn");

    sentenceEl.innerText = sentences[index];

    micBtn.onclick = () => {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = "en-US";

        micBtn.classList.add("recording");
        startTime = Date.now();
        spokenTextEl.innerText = "";

        recognition.onresult = (event) => {
            let interimText = "";

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    rawText += transcript + " ";
                } else {
                    interimText += transcript;
                }
            }
            spokenTextEl.innerText = rawText + interimText;
        };

        recognition.onend = () => {
            micBtn.classList.remove("recording");
            const duration = (Date.now() - startTime) / 1000;

            sendToBackend(rawText.trim(), duration);

            rawText = "";
            spokenTextEl.innerText = "";
        };

        recognition.start();
    };

    function sendToBackend(text, duration) {
        fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                speech: text,
                index: index,
                duration: duration,
                session_id: sessionId
            })
        })
        .then(res => res.json())
        .then(() => {
            if (index < sentences.length - 1) {
                index++;
                sentenceEl.innerText = sentences[index];
            } else {
                sentenceEl.innerText = "Session complete. Preparing results...";
                micBtn.disabled = true;
                showResults();
            }
        });
    }

    function showResults() {
        fetch(`/results/${sessionId}`)
            .then(res => res.json())
            .then(data => {

                const canvas = document.getElementById("resultChart");
                if (!canvas) return;

                new Chart(canvas, {
                    type: "bar",
                    data: {
                        labels: Object.keys(data),
                        datasets: [{
                            label: "Observed Level (0–3)",
                            data: Object.values(data),
                            backgroundColor: "#8e44ad"
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                min: 0,
                                max: 3,
                                ticks: {
                                    stepSize: 1,
                                    callback: v => ["None", "Low", "Medium", "High"][v]
                                }
                            }
                        }
                    }
                });

                localStorage.setItem("session_id", sessionId);

                if (seeBtn) {
                    seeBtn.style.display = "block";
                    seeBtn.onclick = () => {
                        window.location.href = `/final/${sessionId}`;
                    };
                }
            });
    }
}

if (path.startsWith("/final/")) {

    const sessionId = path.split("/").pop();

    fetch(`/results/${sessionId}`)
        .then(res => res.json())
        .then(normalized => {
            return fetch("/final_results", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    stuttering: normalized.Stuttering,
                    hesitation: normalized.Hesitation,
                    pace: normalized.Pace,
                    clarity: normalized.Clarity,
                    articulation: normalized.Articulation
                })
            });
        })
        .then(res => res.json())
        .then(finalData => {

            document.getElementById("fluency-score").innerText =
                finalData.fluency_score;

            document.getElementById("verdict").innerText =
                finalData.verdict;

            document.getElementById("weak-area").innerText =
                finalData.training_plan.weak_area;

            document.getElementById("exercise").innerText =
                finalData.training_plan.exercise;

            const feedbackDiv = document.getElementById("feedback");
            feedbackDiv.innerHTML = "";

            for (let key in finalData.feedback) {
                const p = document.createElement("p");
                p.innerText = "• " + finalData.feedback[key];
                feedbackDiv.appendChild(p);
            }
        });
}
