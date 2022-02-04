import pandas as pd
import plotly.graph_objects as go
import plotly.offline as pyo
import plotly.io as pio
from pathlib import Path


class OutputGraph:

    def __init__(self):
        self.graph = self.build_graph()

    @staticmethod
    def build_graph():
        path = str(Path().resolve().parent) + "\\simulation_files\\myout.csv"
        df = pd.read_csv(path)
        # print(df[:5])
        # print(df.columns.tolist())
        pio.renderers.default = 'browser'

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Timeslot'], y=df['Predicted_load_MW'], name='Maximum capacity',
                                 line=dict(color='firebrick', width=3,
                                           dash='dash')))
        fig.add_trace(go.Scatter(x=df['Timeslot'], y=df['fcfs_load'], name='Load without Scheduling  ',
                                 line=dict(color='royalblue', width=2)))
        fig.add_trace(go.Scatter(x=df['Timeslot'], y=df['std_load'], name='Load with Scheduling',
                                 line=dict(color='green',
                                           width=2)))

        # fig.add_trace(
        #     go.Table(
        #         header=dict(values=list(df.columns),
        #                     fill_color='gray',
        #                     align='left'),
        #         cells=dict(values=[df.Timeslot, df.Predicted_load_MW, df.fcfs_load, df.std_load],
        #                    fill_color='lavender',
        #                    align='left')
        #     ),
        #     row=2, col=1
        # )

        fig.update_layout(title="Charging station profile with/without scheduler",
                          plot_bgcolor='rgb(230, 230,230)',
                          xaxis={'title': 'Timeslot (1 / 15 minutes)', 'fixedrange': True},
                          yaxis={'title': 'Grid Load (MW)', 'fixedrange': True},
                          selectdirection='v',
                          font_family='Courier New',
                          template='plotly_dark',
                          margin=dict(
                              l=90,
                              r=20,
                              b=90,
                              t=100,
                              pad=10
                          ),
                          width=1400,  # figure width in pixels
                          height=720,  # figure height pixels
                          showlegend=True)

        #graph = pyo.plot(fig, filename='chargingprofile.html')
        return pio.show(fig)



# show_graph = Output_graph()
# show_graph.__init__()
# fig.show()
