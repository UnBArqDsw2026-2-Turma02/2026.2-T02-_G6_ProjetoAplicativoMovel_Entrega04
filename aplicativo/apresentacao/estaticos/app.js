document.addEventListener("alpine:init", () => {
  Alpine.store("avisos", {
    lista: [],
    proximoIdentificador: 1,
    exibir(titulo, mensagem, tipo = "informacao") {
      const identificador = this.proximoIdentificador++;
      this.lista.push({ identificador, titulo, mensagem, tipo });
      setTimeout(() => this.remover(identificador), 5000);
    },
    remover(identificador) {
      this.lista = this.lista.filter((aviso) => aviso.identificador !== identificador);
    },
  });
});

async function chamarApi(metodo, caminho, corpo) {
  const opcoes = { method: metodo, headers: { "Content-Type": "application/json" } };
  if (corpo !== undefined) {
    opcoes.body = JSON.stringify(corpo);
  }
  let resposta;
  try {
    resposta = await fetch(caminho, opcoes);
  } catch {
    return { ok: false, conteudo: { erro: "Não foi possível conectar ao servidor." } };
  }
  const tipoConteudo = resposta.headers.get("content-type") || "";
  if (!tipoConteudo.includes("application/json")) {
    return { ok: false, conteudo: { erro: `O servidor respondeu com erro ${resposta.status}.` } };
  }
  const conteudo = await resposta.json();
  if (resposta.status === 401) {
    window.location.href = "/";
  }
  return { ok: resposta.ok, conteudo };
}

function avisar(titulo, mensagem, tipo) {
  Alpine.store("avisos").exibir(titulo, mensagem, tipo);
}

function formatarMoeda(valor) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formularioEndereco(unidadeFederativa, placa) {
  return {
    ufDestino: "DF",
    cep: "",
    logradouro: "",
    caixaPostal: false,
    enviando: false,
    enderecoAtualizado: null,
    async enviar() {
      this.enviando = true;
      const { ok, conteudo } = await chamarApi("PUT", `/api/v1/ufs/${unidadeFederativa}/veiculos/${placa}/endereco`, {
        uf: this.ufDestino,
        cep: this.cep,
        logradouro: this.logradouro,
        caixa_postal: this.caixaPostal,
      });
      this.enviando = false;
      if (ok) {
        this.enderecoAtualizado = conteudo.dados.endereco;
        avisar("Endereço atualizado", conteudo.mensagem, "sucesso");
      } else {
        avisar("Alteração não permitida", conteudo.erro, "erro");
      }
    },
  };
}

function emissaoCrlve(unidadeFederativa, placa, exercicioPadrao) {
  return {
    exercicio: exercicioPadrao,
    emitindo: false,
    documento: null,
    pendencias: [],
    estadoPrototipo: null,
    async iniciar() {
      await this.carregarPrototipo();
    },
    async emitir() {
      this.emitindo = true;
      const { ok, conteudo } = await chamarApi("POST", `/api/v1/ufs/${unidadeFederativa}/veiculos/${placa}/crlve`, {
        exercicio: Number(this.exercicio),
      });
      this.emitindo = false;
      if (ok) {
        this.documento = conteudo.dados.documento;
        this.pendencias = [];
        avisar("CRLV-e emitido", conteudo.mensagem, "sucesso");
      } else {
        this.documento = null;
        this.pendencias = (conteudo.dados && conteudo.dados.pendencias) || [];
        avisar("Emissão bloqueada", conteudo.erro, "erro");
      }
      await this.carregarPrototipo();
    },
    async carregarPrototipo() {
      const { ok, conteudo } = await chamarApi("GET", "/api/v1/documentos/crlve/prototipo");
      if (ok) {
        this.estadoPrototipo = conteudo;
      }
    },
  };
}

function verificacaoTei(unidadeFederativa, placa) {
  return {
    cpfComprador: "",
    verificando: false,
    resultado: null,
    mensagem: "",
    async verificar() {
      this.verificando = true;
      const { ok, conteudo } = await chamarApi(
        "POST",
        `/api/v1/ufs/${unidadeFederativa}/veiculos/${placa}/elegibilidade-tei`,
        { cpf_comprador: this.cpfComprador }
      );
      this.verificando = false;
      if (!ok) {
        avisar("Verificação não realizada", conteudo.erro, "erro");
        return;
      }
      this.resultado = conteudo.dados;
      this.mensagem = conteudo.mensagem;
      const tipoAviso = this.resultado.proximo_passo === "execucao_tei" ? "sucesso" : "alerta";
      avisar("Elegibilidade verificada", conteudo.mensagem, tipoAviso);
    },
  };
}

function solicitacaoDesconto(identificadorInfracao, infracaoInicial) {
  return {
    infracao: infracaoInicial,
    percentualEscolhido: null,
    termoAceito: false,
    enviando: false,
    get exigeTermo() {
      return this.percentualEscolhido === 40;
    },
    async solicitar() {
      this.enviando = true;
      const { ok, conteudo } = await chamarApi("POST", `/api/v1/cidadao/infracoes/${identificadorInfracao}/descontos`, {
        percentual: this.percentualEscolhido,
        termo_aceito: this.termoAceito,
      });
      this.enviando = false;
      if (ok) {
        this.infracao = conteudo.dados.infracao;
        avisar("Desconto aplicado", conteudo.mensagem, "sucesso");
      } else {
        avisar("Desconto não aplicado", conteudo.erro, "erro");
      }
    },
  };
}

function adesaoSne(aderiuInicialmente) {
  return {
    aderiu: aderiuInicialmente,
    tipoDocumento: "cnh",
    numeroCnh: "",
    codigoSegurancaCnh: "",
    placa: "",
    renavam: "",
    numeroSegurancaCrv: "",
    enviando: false,
    protocolo: "",
    async aderir() {
      this.enviando = true;
      const { ok, conteudo } = await chamarApi("POST", "/api/v1/cidadao/sne/adesao", {
        tipo_documento: this.tipoDocumento,
        numero_cnh: this.numeroCnh,
        codigo_seguranca_cnh: this.codigoSegurancaCnh,
        placa: this.placa,
        renavam: this.renavam,
        numero_seguranca_crv: this.numeroSegurancaCrv,
      });
      this.enviando = false;
      if (ok) {
        this.aderiu = true;
        this.protocolo = conteudo.dados.adesao.protocolo;
        avisar("Adesão confirmada", conteudo.mensagem, "sucesso");
      } else {
        avisar("Adesão não realizada", conteudo.erro, "erro");
      }
    },
  };
}
