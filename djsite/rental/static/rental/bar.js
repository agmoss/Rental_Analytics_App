Plotly.d3.json('http://127.0.0.1:8000/api/scatter_data', function(data){

    let xData = [];
    let yData = [];
      
    data.forEach(function(item){

        xData.push(item.community);
        yData.push(item.price__avg);

    });

    let trace = {
        x: xData,
        y: yData,

        marker: {
            color: 'rgba(44, 160, 101, 0.5)'},
            type:'bar',
        }

        let layout = {
            //title: "Average Price Per Community",
            yaxis: {
                title: {
                  text: 'y Axis',
                  font: {
                    family: customPlotLayout.axis.axisFont,
                    size: customPlotLayout.axis.axisTitleSize,
                    color: customPlotLayout.axis.axisColor,
                  }
                },
                tickcolor: customPlotLayout.axis.axisColor,
                tickfont: {
                    family: customPlotLayout.axis.axisFont,
                    size: customPlotLayout.axis.axisTickSize,
                    color: customPlotLayout.axis.axisColor
                  },
              },
              xaxis: {
                title: {
                  text: 'x Axis',
                  font: {
                    family: customPlotLayout.axis.axisFont,
                    size: customPlotLayout.axis.axisTitleSize,
                    color: customPlotLayout.axis.axisColor
                  }
                },
                tickcolor: customPlotLayout.axis.axisColor,
                tickfont: {
                    family: customPlotLayout.axis.axisFont,
                    size: customPlotLayout.axis.axisTickSize,
                    color: customPlotLayout.axis.axisColor
                  },
              },
            plot_bgcolor:customPlotLayout.background.plotBackgroundColor,
            paper_bgcolor:customPlotLayout.background.paperBackgroundColor,

            margin: {
                l: 50,
                r: 10,
                b: 50,
                t: 1,
                pad: 4
              },
        }

    Plotly.plot(document.getElementById("bar_chart"), [trace],layout,  {displayModeBar: false}); 

})