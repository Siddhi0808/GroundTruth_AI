async function loadDashboard() {

    const statsResponse = await fetch(
        "http://127.0.0.1:8000/stats"
    );

    const stats = await statsResponse.json();


    document.getElementById("documents").innerText =
        stats.documents;

    document.getElementById("chunks").innerText =
        stats.chunks;

    document.getElementById("detections").innerText =
        stats.detections;

    document.getElementById("hallucinations").innerText =
        stats.hallucinations;



    const historyResponse = await fetch(
        "http://127.0.0.1:8000/history"
    );


    const history = await historyResponse.json();


    const historyDiv =
        document.getElementById("history");


    historyDiv.innerHTML = "";


    history.forEach(item => {

        const card = document.createElement("div");

        card.className = "history-card";


        card.innerHTML = `

            <h3>${item.verdict}</h3>

            <p>
            ${item.query}
            </p>

            <p>
            Confidence:
            ${item.confidence}%
            </p>

        `;


        historyDiv.appendChild(card);

    });


}


loadDashboard();