import flet as ft
import database as db
from models import Lancamento

def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def main(page: ft.Page):
    page.title = "Controle Financeiro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 950
    page.window.height = 680
    page.padding = 20

    db.init_db()

    # ---------- Componentes do formulário ----------
    txt_descricao = ft.TextField(label="Descrição", width=220)
    txt_valor = ft.TextField(label="Valor (R$)", width=130, keyboard_type=ft.KeyboardType.NUMBER)
    ddl_tipo = ft.Dropdown(label="Tipo", width=140, value="receita",
                           options=[ft.dropdown.Option("receita"), ft.dropdown.Option("despesa")])
    txt_categoria = ft.TextField(label="Categoria", width=160, value="Geral")
    txt_data = ft.TextField(label="Data (AAAA-MM-DD)", width=170,
                            value=__import__("datetime").datetime.now().strftime("%Y-%m-%d"))
    btn_salvar = ft.Button("Salvar", icon=ft.Icons.SAVE)

    form_fields = [txt_descricao, txt_valor, ddl_tipo, txt_categoria, txt_data]

    # ---------- Área de exibição ----------
    cards_saldo = ft.Row([], wrap=True, spacing=12)
    tabela = ft.Column([], scroll=ft.ScrollMode.AUTO, expand=True)
    filtro = ft.Dropdown(label="Filtrar", width=150, value="todos",
                         options=[ft.dropdown.Option("todos"), ft.dropdown.Option("receita"),
                                  ft.dropdown.Option("despesa")],
                         on_select=lambda e: refresh())

    # ---------- Funções de atualização ----------
    def refresh():
        lancamentos = db.listar(filtro.value)
        saldo = db.saldo_atual()
        receitas = sum(l.valor for l in db.listar() if l.tipo == "receita")
        despesas = sum(l.valor for l in db.listar() if l.tipo == "despesa")

        cards_saldo.controls.clear()
        for label, valor, cor in [("Saldo", saldo, ft.Colors.BLUE),
                                   ("Receitas", receitas, ft.Colors.GREEN),
                                   ("Despesas", despesas, ft.Colors.RED)]:
            cards_saldo.controls.append(
                ft.Card(content=ft.Container(ft.Column([
                    ft.Text(label, size=14, color=ft.Colors.GREY_700),
                    ft.Text(brl(valor), size=22, weight=ft.FontWeight.BOLD, color=cor),
                ]), padding=15))
            )

        tabela.controls.clear()
        for l in lancamentos:
            cor = ft.Colors.GREEN if l.tipo == "receita" else ft.Colors.RED
            tabela.controls.append(
                ft.Row([
                    ft.Text(l.data, width=100),
                    ft.Text(l.descricao, width=200),
                    ft.Text(l.categoria, width=130),
                    ft.Text(brl(l.valor), width=120, color=cor, weight=ft.FontWeight.BOLD),
                    ft.IconButton(ft.Icons.EDIT, on_click=lambda e, lan=l: abrir_edicao(lan)),
                    ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED,
                                  on_click=lambda e, id_=l.id: excluir_item(id_)),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )
        page.update()

    # ---------- CRUD ----------
    def salvar(e):
        try:
            valor = float(txt_valor.value.replace(",", "."))
        except ValueError:
            page.open(ft.SnackBar(ft.Text("Valor inválido!")))
            return
        db.adicionar(Lancamento(descricao=txt_descricao.value, valor=valor,
                                tipo=ddl_tipo.value, categoria=txt_categoria.value,
                                data=txt_data.value))
        limpar_form()
        refresh()

    def limpar_form():
        for c in form_fields:
            if isinstance(c, ft.TextField):
                c.value = ""
        txt_categoria.value = "Geral"

    def excluir_item(id_):
        db.excluir(id_)
        refresh()

    # ---------- Edição em diálogo ----------
    def abrir_edicao(l: Lancamento):
        campos = {
            "descricao": ft.TextField(label="Descrição", value=l.descricao),
            "valor": ft.TextField(label="Valor", value=str(l.valor)),
            "tipo": ft.Dropdown(label="Tipo", value=l.tipo,
                                options=[ft.dropdown.Option("receita"), ft.dropdown.Option("despesa")]),
            "categoria": ft.TextField(label="Categoria", value=l.categoria),
            "data": ft.TextField(label="Data", value=l.data),
        }

        def confirmar(e):
            l.descricao = campos["descricao"].value
            l.valor = float(campos["valor"].value.replace(",", "."))
            l.tipo = campos["tipo"].value
            l.categoria = campos["categoria"].value
            l.data = campos["data"].value
            db.atualizar(l)
            page.close(dialog)
            refresh()

        dialog = ft.AlertDialog(
            modal=True, title=ft.Text("Editar lançamento"),
            content=ft.Column(list(campos.values()), width=350, tight=True),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dialog)),
                     ft.FilledButton("Salvar", on_click=confirmar)],
        )
        page.open(dialog)

    # ---------- Relatório ----------
    def abrir_relatorio(e):
        linhas = [ft.DataRow(cells=[ft.DataCell(ft.Text("Categoria", bold=True)),
                                     ft.DataCell(ft.Text("Receitas", bold=True)),
                                     ft.DataCell(ft.Text("Despesas", bold=True)),
                                     ft.DataCell(ft.Text("Resultado", bold=True))])]
        for cat, v in db.resumo_por_categoria().items():
            resultado = v["receitas"] - v["despesas"]
            linhas.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(cat)),
                ft.DataCell(ft.Text(brl(v["receitas"]))),
                ft.DataCell(ft.Text(brl(v["despesas"]))),
                ft.DataCell(ft.Text(brl(resultado), color=ft.Colors.GREEN if resultado >= 0 else ft.Colors.RED)),
            ]))
        dialog = ft.AlertDialog(
            title=ft.Text("Relatório por Categoria"),
            content=ft.Column([ft.DataTable(columns=[], rows=linhas)], scroll=ft.ScrollMode.AUTO),
            actions=[ft.TextButton("Fechar", on_click=lambda e: page.close(dialog))],
        )
        page.open(dialog)

    btn_salvar.on_click = salvar

    # ---------- Layout final ----------
    page.add(
        ft.Row([ft.Text("💰 Controle Financeiro", size=26, weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.Icons.PIE_CHART, tooltip="Relatório", on_click=abrir_relatorio)]),
        cards_saldo,
        ft.Divider(),
        ft.Row(form_fields + [btn_salvar], wrap=True, vertical_alignment=ft.CrossAxisAlignment.END),
        ft.Row([filtro, ft.Text("Lançamentos", size=18, weight=ft.FontWeight.BOLD)]),
        ft.Row([ft.Text(d, width=w, weight=ft.FontWeight.BOLD) for d, w in
                [("Data", 100), ("Descrição", 200), ("Categoria", 130), ("Valor", 120)]]),
        tabela,
    )
    refresh()

ft.run(main)