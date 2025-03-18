import json  # Добавлен импорт модуля json
import networkx as nx
import plotly.graph_objects as go
import matplotlib.colors as mcolors


def visualize_with_plotly(G):
    """
    Визуализирует граф с помощью Plotly.
    Добавляет жирные красные линии между компаниями с общими участниками/директорами.
    """
    pos = nx.spring_layout(G, seed=42, k=0.5)

    # Генерация уникальных цветов для физических лиц
    people = [node for node, attr in G.nodes(data=True) if attr.get("type") == "person"]
    colors = list(mcolors.TABLEAU_COLORS.values())  # Используем стандартные цвета
    color_map = {person: colors[i % len(colors)] for i, person in enumerate(people)}

    edge_traces = []

    # Нахождение связей между компаниями через общих участников/директоров
    from graph_operations import find_common_connections
    common_connections = find_common_connections(G)

    # Обработка обычных связей
    for edge in G.edges(data=True):
        person, company, data = edge
        relation_type = data["relation"]
        x0, y0 = pos[person]
        x1, y1 = pos[company]
        edge_color = color_map[person]  # Цвет определяется по физическому лицу
        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            line=dict(width=2, color=edge_color),
            hoverinfo="text",
            mode="lines",
            text=f"{person.upper()} ({relation_type}) -> {company.upper()}",  # Преобразование в верхний регистр
            textposition="top center"
        )
        edge_traces.append(edge_trace)

    # Добавление жирных красных линий между компаниями с общими участниками/директорами
    for (company1, company2), common_people in common_connections.items():
        x0, y0 = pos[company1]
        x1, y1 = pos[company2]
        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            line=dict(width=4, color="red"),
            hoverinfo="text",
            mode="lines",
            text=f"Общие связи: {', '.join(common_people).upper()}",  # Преобразование в верхний регистр
            textposition="top center"
        )
        edge_traces.append(edge_trace)

    # Создание узлов
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_shape = []

    for node, attributes in G.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node.upper()}<br>{attributes.get('type', '').upper()}")  # Преобразование в верхний регистр
        if attributes.get("type") == "company":
            node_color.append("lightblue")
            node_shape.append("square")
        else:
            node_color.append(color_map[node])  # Цвет узла совпадает с цветом связей
            node_shape.append("circle")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=[node.upper() for node in G.nodes()],  # Преобразование в верхний регистр
        textposition="top center",
        hoverinfo="text",
        hovertext=node_text,
        marker=dict(
            size=15,
            color=node_color,
            symbol=node_shape,
            line=dict(width=2, color="black")
        )
    )

    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            title="Граф связей между юридическими и физическими лицами",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )

    fig.show()