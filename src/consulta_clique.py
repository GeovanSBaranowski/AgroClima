from branca.element import MacroElement, Template


class ConsultaPorClique(MacroElement):
    _template = Template("""
        {% macro script(this, kwargs) %}
        const mapaConsulta = {{ this._parent.get_name() }};
        let marcadorConsulta = null;

        mapaConsulta.on("click", async function (evento) {
            const latitude = evento.latlng.lat;
            const longitude = evento.latlng.lng;

            if (marcadorConsulta !== null) {
                mapaConsulta.removeLayer(marcadorConsulta);
            }

            marcadorConsulta = L.marker([latitude, longitude])
                .addTo(mapaConsulta)
                .bindPopup("Consultando ponto...", { minWidth: 220 })
                .openPopup();

            const marcadorDesteClique = marcadorConsulta;

            const parametros = new URLSearchParams({
                latitude: latitude,
                longitude: longitude
            });

            try {
                const resposta = await fetch(
                    "/api/ponto?" + parametros.toString()
                );

                if (!resposta.ok) {
                    throw new Error("Falha na consulta");
                }

                const dados = await resposta.json();

                if (marcadorDesteClique !== marcadorConsulta) {
                    return;
                }

                const conteudo = document.createElement("div");
                conteudo.style.whiteSpace = "pre-line";

                const textoNdvi = dados.ndvi === null
                    ? "Indisponível neste ponto"
                    : dados.ndvi.toFixed(4);

                const textoElevacao = dados.elevacao === null
                    ? "Indisponível neste ponto"
                    : dados.elevacao.toFixed(2) + " m";

                const textoInclinacao = dados.inclinacao === null
                    ? "Indisponível neste ponto"
                    : dados.inclinacao.toFixed(2) + " graus";

                let linhasSolo;

                if (dados.solo === null) {
                    linhasSolo = ["Solo: arquivo não informado"];
                } else if (dados.solo.length === 0) {
                    linhasSolo = ["Solo: nenhuma unidade encontrada"];
                } else {
                    linhasSolo = dados.solo.map(function (unidade) {
                        return "Solo: " + unidade.categoria + " — " + unidade.legenda;
                    });
                }

                conteudo.textContent = [
                    "Ponto selecionado",
                    "Latitude: " + dados.latitude.toFixed(4),
                    "Longitude: " + dados.longitude.toFixed(4),
                    "NDVI: " + textoNdvi,
                    "Data informada no NDVI (UTC): " + (dados.data_ndvi || "não informada"),
                    "Elevação: " + textoElevacao,
                    "Inclinação: " + textoInclinacao,
                    ...linhasSolo
                ].join(String.fromCharCode(10));

                marcadorConsulta.setPopupContent(conteudo);

            } catch (erro) {

                if (marcadorDesteClique !== marcadorConsulta) {
                    return;
                }

                marcadorConsulta.setPopupContent(
                    "Não foi possível consultar o ponto."
                );
            }
        });
        {% endmacro %}
    """)

    def __init__(self):
        super().__init__()
        self._name = "ConsultaPorClique"