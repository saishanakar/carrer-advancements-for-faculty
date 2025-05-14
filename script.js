document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("predictButton").addEventListener("click", function (event) {
        let inputData = {
            "Years of Service": parseInt(document.getElementById("years").value),
            "Patent Count": parseInt(document.getElementById("patents").value),
            "Publication Records (Journals)": parseInt(document.getElementById("journals").value),
            "Publication Records (Conferences)": parseInt(document.getElementById("conferences").value),
            "Student Engagement (1-10)": parseInt(document.getElementById("engagement").value),
            "Doubt Resolution (1-10)": parseInt(document.getElementById("doubt").value),
            "Teaching Innovation Metrics (1-10)": parseInt(document.getElementById("innovation").value),
            "Student Success Rates (1-10)": parseInt(document.getElementById("success").value)
        };

        console.log("Sending Data:", inputData); // Debugging Log

        fetch("http://127.0.0.1:5001/predict", {
            // Make sure it's 5001
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(inputData)
        })
        
        .then(response => response.json())
        .then(data => {
            console.log("Response Data:", data);  // Debugging
            document.getElementById("result").innerHTML = `
                <p>Predicted Designation: <strong>${data["Predicted Designation"]}</strong></p>
                <p>Recommendation: <strong>${data.Recommendation}</strong></p>
            `;
        })        
        .catch(error => {
            console.error("Fetch Error:", error);
            document.getElementById("result").innerHTML = "<p style='color:red;'>Error in prediction.</p>";
        });
    });
});
