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
        resultBox.textContent = `Current simulated recommendation: Option ${data.recommendation}, ${data.recommendation_name}`;
      }
    } catch (error) {
      if (resultBox) {
        resultBox.textContent = "Simulation failed. The backend may not be running.";
      }
    }
  }

  sliders.forEach((slider) => {
    slider.addEventListener("input", simulate);
  });

  simulate();
})();
