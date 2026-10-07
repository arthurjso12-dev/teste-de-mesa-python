import ast
import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext, ttk

from mesa_automatica import MesaTracer, format_table


EXEMPLO_CODIGO = '''# Exemplo de teste de mesa
x = int(input("Digite um número: "))
y = x + 5

if y > 10:
    print("Maior que 10")
else:
    print("Menor ou igual a 10")

for i in range(3):
    print(i)
'''


class AplicativoTesteMesa:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Teste de Mesa - Automático")
        self.root.geometry("1100x760")
        self.root.minsize(900, 600)
        self.root.configure(bg="#0b1120")

        self.estilo()
        self.criar_interface()
        self._atualizar_historico()

    def estilo(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Titulo.TLabel", font=("Segoe UI", 22, "bold"), foreground="#e2e8f0", background="#0b1120")
        style.configure("Subtitulo.TLabel", font=("Segoe UI", 11), foreground="#cbd5e1", background="#0b1120")
        style.configure("Campo.TLabel", font=("Segoe UI", 10, "bold"), foreground="#e2e8f0", background="#0b1120")
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"), foreground="#cbd5e1", background="#111827")
        style.configure("BotaoExecutar.TButton", font=("Segoe UI", 10, "bold"), background="#3b82f6", foreground="#f8fafc")
        style.configure("BotaoSecundario.TButton", font=("Segoe UI", 10), background="#1e293b", foreground="#f8fafc")
        style.map("BotaoExecutar.TButton", background=[("active", "#2563eb")])
        style.map("BotaoSecundario.TButton", background=[("active", "#334155")])

    def criar_interface(self):
        container = tk.Frame(self.root, bg="#0b1120")
        container.pack(fill="both", expand=True, padx=18, pady=18)

        titulo = ttk.Label(container, text="Teste de Mesa Automático", style="Titulo.TLabel")
        titulo.pack(anchor="w", pady=(0, 4))

        subtitulo = ttk.Label(
            container,
            text="Digite o código, informe os valores de entrada e veja o passo a passo da execução.",
            style="Subtitulo.TLabel",
        )
        subtitulo.pack(anchor="w", pady=(0, 16))

        painel_topo = tk.Frame(container, bg="#0b1120")
        painel_topo.pack(fill="x", pady=(0, 10))

        lbl_entradas = ttk.Label(painel_topo, text="Entradas (separadas por vírgula):", style="Campo.TLabel")
        lbl_entradas.pack(anchor="w")

        self.entradas_var = tk.StringVar(value="7")
        self.entrada = ttk.Entry(
            painel_topo,
            textvariable=self.entradas_var,
            font=("Segoe UI", 11),
            width=60,
        )
        self.entrada.pack(fill="x", pady=(6, 0))

        modo_frame = tk.Frame(container, bg="#0b1120")
        modo_frame.pack(fill="x", pady=(8, 0))

        ttk.Label(modo_frame, text="Modo:", style="Campo.TLabel").pack(side="left", padx=(0, 10))
        self.modo_var = tk.StringVar(value="Aluno")
        self.modo_aluno = ttk.Radiobutton(modo_frame, text="Aluno", variable=self.modo_var, value="Aluno")
        self.modo_aluno.pack(side="left", padx=(0, 12))
        self.modo_professor = ttk.Radiobutton(modo_frame, text="Professor", variable=self.modo_var, value="Professor")
        self.modo_professor.pack(side="left")

        self.info_modo = ttk.Label(
            modo_frame,
            text="Aluno = foco no aprendizado e passo a passo. Professor = visão rápida e controle do histórico.",
            style="Subtitulo.TLabel",
        )
        self.info_modo.pack(side="left", padx=(16, 0))

        categoria_frame = tk.Frame(container, bg="#0b1120")
        categoria_frame.pack(fill="x", pady=(12, 0))

        ttk.Label(categoria_frame, text="Categoria do exemplo:", style="Campo.TLabel").pack(side="left", padx=(0, 10))
        self.categoria_var = tk.StringVar(value="Geral")
        self.categoria_combo = ttk.Combobox(
            categoria_frame,
            textvariable=self.categoria_var,
            values=["Geral", "Condicional", "Laço", "Lista", "Função", "Entrada/Saída"],
            state="readonly",
            width=20,
        )
        self.categoria_combo.pack(side="left")

        botoes = tk.Frame(container, bg="#0b1120")
        botoes.pack(fill="x", pady=(14, 12))

        btn_abrir = ttk.Button(botoes, text="Abrir arquivo", command=self.abrir_arquivo, style="BotaoSecundario.TButton")
        btn_abrir.pack(side="left", padx=(0, 10))

        btn_exemplo = ttk.Button(botoes, text="Carregar exemplo", command=self.carregar_exemplo, style="BotaoSecundario.TButton")
        btn_exemplo.pack(side="left", padx=(0, 10))

        btn_executar = ttk.Button(botoes, text="Executar teste de mesa", command=self.executar, style="BotaoExecutar.TButton")
        btn_executar.pack(side="left", padx=(0, 10))

        btn_limpar_codigo = ttk.Button(botoes, text="Limpar código", command=self.limpar_codigo, style="BotaoSecundario.TButton")
        btn_limpar_codigo.pack(side="left", padx=(0, 10))

        btn_salvar_exemplo = ttk.Button(botoes, text="Salvar exemplo", command=self.salvar_exemplo_historico, style="BotaoSecundario.TButton")
        btn_salvar_exemplo.pack(side="left", padx=(0, 10))

        btn_salvar_resultado = ttk.Button(botoes, text="Salvar resultado", command=self.salvar_resultado, style="BotaoSecundario.TButton")
        btn_salvar_resultado.pack(side="left", padx=(0, 10))

        btn_copiar = ttk.Button(botoes, text="Copiar resultado", command=self.copiar_resultado, style="BotaoSecundario.TButton")
        btn_copiar.pack(side="left", padx=(0, 10))

        btn_limpar = ttk.Button(botoes, text="Limpar saída", command=self.limpar_resultado, style="BotaoSecundario.TButton")
        btn_limpar.pack(side="left")

        painel_codigo = tk.Frame(container, bg="#111827", bd=1, relief="solid")
        painel_codigo.pack(fill="both", expand=True)

        headers = tk.Frame(painel_codigo, bg="#111827")
        headers.pack(fill="x", padx=12, pady=(12, 6))

        lbl_codigo = ttk.Label(headers, text="Código Python", style="Campo.TLabel")
        lbl_codigo.pack(anchor="w")

        self.codigo = scrolledtext.ScrolledText(
            painel_codigo,
            wrap=tk.WORD,
            font=("Consolas", 11),
            height=7,
            padx=10,
            pady=10,
            bg="#0f172a",
            fg="#e2e8f0",
            insertbackground="#f8fafc",
        )
        self.codigo.pack(fill="x", padx=12, pady=(0, 12))
        self.codigo.insert(tk.END, EXEMPLO_CODIGO)

        historico_frame = tk.Frame(container, bg="#111827", bd=1, relief="solid")
        historico_frame.pack(fill="x", pady=(0, 12))

        lbl_historico = ttk.Label(historico_frame, text="Histórico de exemplos", style="Campo.TLabel")
        lbl_historico.pack(anchor="w", padx=12, pady=(12, 6))

        self.historico_itens = []
        self.historico_listbox = tk.Listbox(
            historico_frame,
            height=3,
            font=("Segoe UI", 10),
            activestyle="none",
            exportselection=False,
            bg="#0f172a",
            fg="#e2e8f0",
            selectbackground="#1d4ed8",
            selectforeground="#f8fafc",
        )
        self.historico_listbox.pack(fill="x", padx=12, pady=(0, 12))
        self.historico_listbox.bind("<<ListboxSelect>>", self.carregar_item_historico)
        self._atualizar_historico()

        resultado_frame = tk.Frame(container, bg="#111827", bd=1, relief="solid")
        resultado_frame.pack(fill="both", expand=True)

        cabecalho_resultado = tk.Frame(resultado_frame, bg="#111827")
        cabecalho_resultado.pack(fill="x", padx=12, pady=(12, 6))

        lbl_resultado = ttk.Label(cabecalho_resultado, text="Resultado do teste de mesa", style="Campo.TLabel")
        lbl_resultado.pack(side="left", anchor="w")

        self.status_resultado = ttk.Label(
            cabecalho_resultado,
            text="Aguardando execução",
            style="Status.TLabel",
        )
        self.status_resultado.pack(side="right", anchor="e")

        self.resultado = scrolledtext.ScrolledText(
            resultado_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            height=10,
            padx=10,
            pady=10,
            bg="#020817",
            fg="#e2e8f0",
            insertbackground="#f8fafc",
        )
        self.resultado.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.resultado.insert(tk.END, "A tabela com a conta passo a passo aparecerá aqui após a execução.\n")

    def _definir_status(self, texto, cor="#cbd5e1"):
        self.status_resultado.configure(text=texto, foreground=cor)

    def carregar_exemplo(self):
        self.codigo.delete("1.0", tk.END)
        self.codigo.insert(tk.END, EXEMPLO_CODIGO)
        self.entradas_var.set("7")
        self._definir_status("Exemplo carregado; aguardando execução")
        self.resultado.delete("1.0", tk.END)
        self.resultado.insert(tk.END, "A tabela com a conta passo a passo aparecerá aqui após a execução.\n")

    def _caminho_historico(self):
        return os.path.join(os.path.dirname(__file__), "historico_teste_mesa.json")

    def _carregar_historico(self):
        caminho = self._caminho_historico()
        if not os.path.exists(caminho):
            return []
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
                if isinstance(dados, list):
                    return dados
        except (json.JSONDecodeError, OSError):
            return []
        return []

    def _salvar_historico(self, itens):
        caminho = self._caminho_historico()
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(itens, arquivo, ensure_ascii=False, indent=2)

    def _atualizar_historico(self):
        self.historico_itens = self._carregar_historico()
        self.historico_listbox.delete(0, tk.END)
        for item in self.historico_itens:
            categoria = item.get("categoria", "Geral")
            titulo = item.get("titulo", "Exemplo")
            self.historico_listbox.insert(tk.END, f"[{categoria}] {titulo}")

    def salvar_exemplo_historico(self):
        codigo = self.codigo.get("1.0", tk.END).strip()
        if not codigo:
            messagebox.showwarning("Código vazio", "Digite um código antes de salvar no histórico.")
            return

        historico = self._carregar_historico()
        preview = codigo.strip().splitlines()[0][:45]
        if len(preview) == 45:
            preview = preview + "..."

        item = {
            "titulo": preview,
            "codigo": codigo,
            "categoria": self.categoria_var.get(),
            "modo": self.modo_var.get(),
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        historico = [item] + [entry for entry in historico if entry.get("codigo") != codigo]
        historico = historico[:8]
        self._salvar_historico(historico)
        self._atualizar_historico()
        messagebox.showinfo("Sucesso", "Exemplo salvo no histórico.")

    def carregar_item_historico(self, event=None):
        if not hasattr(self, "historico_listbox"):
            return
        selecao = self.historico_listbox.curselection()
        if not selecao:
            return
        item = self.historico_itens[selecao[0]]
        self.codigo.delete("1.0", tk.END)
        self.codigo.insert(tk.END, item.get("codigo", ""))
        self.categoria_var.set(item.get("categoria", "Geral"))
        self.modo_var.set(item.get("modo", "Aluno"))
        self._definir_status("Exemplo carregado; aguardando execução")
        self.resultado.delete("1.0", tk.END)
        self.resultado.insert(tk.END, "A tabela com a conta passo a passo aparecerá aqui após a execução.\n")

    def limpar_codigo(self):
        self.codigo.delete("1.0", tk.END)
        self._definir_status("Aguardando execução")
        self.resultado.delete("1.0", tk.END)
        self.resultado.insert(tk.END, "A tabela com a conta passo a passo aparecerá aqui após a execução.\n")

    def abrir_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Abrir arquivo Python",
            filetypes=[("Arquivos Python", "*.py"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return

        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                codigo = arquivo.read()
            self.codigo.delete("1.0", tk.END)
            self.codigo.insert(tk.END, codigo)
            self._definir_status("Arquivo carregado; aguardando execução")
            self.resultado.delete("1.0", tk.END)
            self.resultado.insert(tk.END, "A tabela com a conta passo a passo aparecerá aqui após a execução.\n")
        except OSError as exc:
            messagebox.showerror("Erro ao abrir arquivo", str(exc))

    def salvar_resultado(self):
        texto = self.resultado.get("1.0", tk.END)
        if not texto.strip():
            messagebox.showwarning("Resultado vazio", "Não há resultado para salvar.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar resultado",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return

        try:
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write(texto)
            messagebox.showinfo("Sucesso", f"Resultado salvo em:\n{caminho}")
        except OSError as exc:
            messagebox.showerror("Erro ao salvar", str(exc))

    def copiar_resultado(self):
        texto = self.resultado.get("1.0", tk.END).strip()
        if not texto:
            messagebox.showwarning("Resultado vazio", "Não há texto para copiar.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        messagebox.showinfo("Sucesso", "Resultado copiado para a área de transferência.")

    def limpar_resultado(self):
        self.resultado.delete("1.0", tk.END)
        self._definir_status("Aguardando execução")
        self.resultado.insert(tk.END, "A tabela com a conta passo a passo aparecerá aqui após a execução.\n")

    def verificar_codigo(self, codigo: str):
        try:
            ast.parse(codigo)
            return True, "Código válido."
        except SyntaxError as exc:
            mensagem = (
                f"Erro de sintaxe: {exc.msg}\n"
                f"Linha {exc.lineno}, coluna {exc.offset}"
            )
            return False, mensagem

    def executar(self):
        codigo = self.codigo.get("1.0", tk.END).strip()
        entradas = self.entradas_var.get().strip()

        if not codigo:
            messagebox.showwarning("Código vazio", "Digite um código Python antes de executar.")
            return

        valido, mensagem = self.verificar_codigo(codigo)
        if not valido:
            self._definir_status("CÓDIGO INVÁLIDO", "#f87171")
            self.resultado.delete("1.0", tk.END)
            self.resultado.insert(
                tk.END,
                f"Validação de sintaxe: {mensagem}\n\nModo: {self.modo_var.get()}\nCategoria: {self.categoria_var.get()}\n"
            )
            messagebox.showerror("Código inválido", mensagem)
            return

        valores_entrada = [item.strip() for item in entradas.split(',') if item.strip()]

        try:
            tracer = MesaTracer(codigo.splitlines(), valores_entrada)
            tracer.visit(ast.parse(codigo))
            tabela = format_table(tracer.logs)
        except Exception as exc:  # noqa: BLE001
            self._definir_status("ERRO DURANTE A EXECUÇÃO", "#fbbf24")
            self.resultado.delete("1.0", tk.END)
            self.resultado.insert(
                tk.END,
                f"O código passou na validação de sintaxe, mas a conta não pôde ser concluída:\n{exc}\n\nModo: {self.modo_var.get()}\nCategoria: {self.categoria_var.get()}\n"
            )
            messagebox.showerror("Erro durante a execução", f"Não foi possível executar o teste de mesa:\n\n{exc}")
            return

        self.resultado.delete("1.0", tk.END)
        self._definir_status("CÓDIGO VÁLIDO · TESTE CONCLUÍDO", "#4ade80")
        self.resultado.insert(
            tk.END,
            f"{mensagem}\nModo: {self.modo_var.get()}\nCategoria: {self.categoria_var.get()}\n\n{tabela}"
        )
        self.salvar_exemplo_historico()


if __name__ == "__main__":
    root = tk.Tk()
    AplicativoTesteMesa(root)
    root.mainloop()
