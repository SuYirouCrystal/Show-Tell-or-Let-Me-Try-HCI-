(function () {
  const page = document.querySelector(".task-card");
  const form = document.getElementById("response-form");
  const startedAt = Date.now();

  if (form) {
    form.addEventListener("submit", function () {
      const decisionInput = document.getElementById("client_decision_ms");
      if (decisionInput) {
        decisionInput.value = String(Date.now() - startedAt);
      }
    });
  }

  if (!page || page.dataset.condition !== "try") {
    return;
  }

  const taskId = page.dataset.taskId;
  const sliders = Array.from(document.querySelectorAll(".weight-slider"));
  const resultBox = document.getElementById("simulation-result");
  const scoreBreakdown = document.getElementById("score-breakdown");

  function collectWeights() {
    const weights = {};
    sliders.forEach((slider) => {
      weights[slider.dataset.featureId] = Number(slider.value);
      const output = slider.parentElement.querySelector("output");
      if (output) {
        output.textContent = slider.value;
      }
    });
    return weights;
  }

  function renderScores(scores) {
    if (!scoreBreakdown) {
      return;
    }

    scoreBreakdown.replaceChildren();
    scores.forEach((item) => {
      const row = document.createElement("div");
      row.className = "score-row";

      const name = document.createElement("span");
      name.textContent = `Option ${item.option_id}`;

      const track = document.createElement("span");
      track.className = "score-track";

      const fill = document.createElement("span");
      fill.className = "score-fill";
      fill.style.width = `${Math.round(item.score * 100)}%`;
      track.appendChild(fill);

      const score = document.createElement("strong");
      score.textContent = `${Math.round(item.score * 100)}%`;

      row.append(name, track, score);
      scoreBreakdown.appendChild(row);
    });
  }

  async function simulate() {
    const weights = collectWeights();
    try {
      const response = await fetch(`/api/tasks/${taskId}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ weights })
      });
      const data = await response.json();
      if (resultBox) {
        resultBox.textContent = `Current what-if result: Option ${data.recommendation}, ${data.recommendation_name}`;
      }
      renderScores(data.scores || []);
    } catch (error) {
      if (resultBox) {
        resultBox.textContent = "Simulation failed. The backend may not be running.";
      }
      if (scoreBreakdown) {
        scoreBreakdown.replaceChildren();
      }
    }
  }

  sliders.forEach((slider) => {
    slider.addEventListener("input", simulate);
  });

  simulate();
})();
