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

async function copiarTexto(texto, mensagemSucesso) {
  try {
    await navigator.clipboard.writeText(texto);
    avisar("Copiado", mensagemSucesso, "sucesso");
  } catch {
    avisar("Não foi possível copiar", "Selecione o texto e copie manualmente.", "erro");
  }
}

function comEnvio() {
  return {
    enviando: false,
    async enviarParaApi(metodo, caminho, corpo, { tituloSucesso, tituloErro, tipoSucesso = "sucesso" }) {
      this.enviando = true;
      const resposta = await chamarApi(metodo, caminho, corpo);
      this.enviando = false;
      if (resposta.ok) {
        avisar(tituloSucesso, resposta.conteudo.mensagem, tipoSucesso);
      } else {
        avisar(tituloErro, resposta.conteudo.erro, "erro");
      }
      return resposta;
    },
  };
}

function formularioEndereco(unidadeFederativa, placa) {
  return {
    ...comEnvio(),
    ufDestino: "DF",
    cep: "",
    logradouro: "",
    caixaPostal: false,
    enderecoAtualizado: null,
    async enviar() {
      const { ok, conteudo } = await this.enviarParaApi(
        "PUT",
        `/api/v1/ufs/${unidadeFederativa}/veiculos/${placa}/endereco`,
        { uf: this.ufDestino, cep: this.cep, logradouro: this.logradouro, caixa_postal: this.caixaPostal },
        { tituloSucesso: "Endereço atualizado", tituloErro: "Alteração não permitida" }
      );
      if (ok) {
        this.enderecoAtualizado = conteudo.dados.endereco;
      }
    },
  };
}

function emissaoCrlve(unidadeFederativa, placa, exercicioPadrao) {
  return {
    ...comEnvio(),
    exercicio: exercicioPadrao,
    documento: null,
    pendencias: [],
    estadoPrototipo: null,
    async emitir() {
      const { ok, conteudo } = await this.enviarParaApi(
        "POST",
        `/api/v1/ufs/${unidadeFederativa}/veiculos/${placa}/crlve`,
        { exercicio: Number(this.exercicio) },
        { tituloSucesso: "CRLV-e emitido", tituloErro: "Emissão bloqueada" }
      );
      this.documento = ok ? conteudo.dados.documento : null;
      this.pendencias = ok ? [] : (conteudo.dados && conteudo.dados.pendencias) || [];
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
    ...comEnvio(),
    cpfComprador: "",
    resultado: null,
    mensagem: "",
    async verificar() {
      this.enviando = true;
      const { ok, conteudo } = await chamarApi(
        "POST",
        `/api/v1/ufs/${unidadeFederativa}/veiculos/${placa}/elegibilidade-tei`,
        { cpf_comprador: this.cpfComprador }
      );
      this.enviando = false;
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

function painelInfracao(infracaoInicial) {
  const caminhoInfracao = `/api/v1/cidadao/infracoes/${infracaoInicial.identificador}`;
  return {
    ...comEnvio(),
    infracao: infracaoInicial,
    percentualEscolhido: null,
    termoAceito: false,
    cpfCondutor: "",
    cnhCondutor: "",
    declaracaoAceita: false,
    async recarregar() {
      const { ok, conteudo } = await chamarApi("GET", caminhoInfracao);
      if (ok) {
        this.infracao = conteudo;
      }
    },
    async solicitarDesconto() {
      const { ok } = await this.enviarParaApi(
        "POST",
        `${caminhoInfracao}/descontos`,
        { percentual: this.percentualEscolhido, termo_aceito: this.termoAceito },
        { tituloSucesso: "Desconto aplicado", tituloErro: "Desconto não aplicado" }
      );
      if (ok) {
        await this.recarregar();
      }
    },
    async gerarBoleto() {
      const { ok } = await this.enviarParaApi("POST", `${caminhoInfracao}/boleto`, undefined, {
        tituloSucesso: "Boleto",
        tituloErro: "Boleto não gerado",
      });
      if (ok) {
        await this.recarregar();
      }
    },
    async indicarCondutor() {
      const { ok } = await this.enviarParaApi(
        "POST",
        `${caminhoInfracao}/indicacao-condutor`,
        { cpf_condutor: this.cpfCondutor, numero_cnh_condutor: this.cnhCondutor, declaracao_aceita: this.declaracaoAceita },
        { tituloSucesso: "Indicação enviada", tituloErro: "Indicação não enviada" }
      );
      if (ok) {
        await this.recarregar();
      }
    },
  };
}

function acoesDocumento(nomeArquivo) {
  return {
    imprimir() {
      window.print();
    },
    async compartilhar() {
      const dadosCompartilhamento = { title: nomeArquivo, url: window.location.href };
      if (navigator.share) {
        try {
          await navigator.share(dadosCompartilhamento);
        } catch {
          return;
        }
        return;
      }
      await copiarTexto(window.location.href, "Link do boleto copiado para compartilhar.");
    },
  };
}

function adesaoSne(aderiuInicialmente) {
  return {
    ...comEnvio(),
    aderiu: aderiuInicialmente,
    tipoDocumento: "cnh",
    numeroCnh: "",
    codigoSegurancaCnh: "",
    placa: "",
    renavam: "",
    numeroSegurancaCrv: "",
    protocolo: "",
    async aderir() {
      const { ok, conteudo } = await this.enviarParaApi(
        "POST",
        "/api/v1/cidadao/sne/adesao",
        {
          tipo_documento: this.tipoDocumento,
          numero_cnh: this.numeroCnh,
          codigo_seguranca_cnh: this.codigoSegurancaCnh,
          placa: this.placa,
          renavam: this.renavam,
          numero_seguranca_crv: this.numeroSegurancaCrv,
        },
        { tituloSucesso: "Adesão confirmada", tituloErro: "Adesão não realizada" }
      );
      if (ok) {
        this.aderiu = true;
        this.protocolo = conteudo.dados.adesao.protocolo;
      }
    },
  };
}

function painelHabilitacao(estadoInicial) {
  const caminhoHabilitacao = "/api/v1/cidadao/habilitacao";
  return {
    ...comEnvio(),
    estado: estadoInicial,
    categoriaDesejada: "",
    gravidadeSimulada: "leve",
    rotulosResultado: {
      aceita: "aceita",
      recusada: "recusada",
      encaminhada_ao_detran: "encaminhada ao Detran",
    },
    async recarregar() {
      const { ok, conteudo } = await chamarApi("GET", caminhoHabilitacao);
      if (ok) {
        this.estado = conteudo;
      }
    },
    async executar(caminho, corpo, titulos) {
      const resposta = await this.enviarParaApi("POST", `${caminhoHabilitacao}${caminho}`, corpo, titulos);
      await this.recarregar();
      return resposta;
    },
    concluirPeriodo() {
      return this.executar("/conclusao-ppd", undefined, {
        tituloSucesso: "Situação atualizada",
        tituloErro: "Período não concluído",
      });
    },
    iniciarNovaHabilitacao() {
      return this.executar("/reinicio", undefined, {
        tituloSucesso: "Nova PPD",
        tituloErro: "Não foi possível reiniciar",
      });
    },
    registrarInfracao() {
      return this.executar(
        "/infracoes",
        { gravidade: this.gravidadeSimulada },
        { tituloSucesso: "Histórico atualizado", tituloErro: "Infração não registrada", tipoSucesso: "alerta" }
      );
    },
    async solicitarCategoria() {
      const { ok, conteudo } = await this.executar(
        "/alteracoes-categoria",
        { categoria_desejada: this.categoriaDesejada },
        { tituloSucesso: "Pedido validado", tituloErro: "Pedido não validado", tipoSucesso: "informacao" }
      );
      if (ok && conteudo.dados.solicitacao.resultado !== "aceita") {
        avisar("Resultado", conteudo.dados.solicitacao.motivo, "alerta");
      }
    },
  };
}
