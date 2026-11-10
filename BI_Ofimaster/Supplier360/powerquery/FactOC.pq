let
    Source = Csv.Document(File.Contents(pRutaModelo & "FactOC.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumns(Headers, {
        {"FechaPedido", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"FechaCorte", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"FechaPromesaMin", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"FechaPromesaMax", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"CantidadPedida", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"CantidadProgramada", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"CantidadRecibidaAcumulada", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"CantidadCubierta", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"CantidadElegible", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"CantidadFaltante", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"CantidadPendienteAbierta", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"ValorNetoOC", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"ValorPendienteMonedaOC", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"Borrada", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"EntregaFinal", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"ElegibleCompras", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"ElegibleFillRate", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"Repartos", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"DescuadreRepartos", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"ProveedorEnMaestro", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"ProductoEnMaestro", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"CantidadEntregadaVista", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"FechaEmbarqueCandidata", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"FechaArriboCandidata", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"OTIFEvaluable", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"OTIFCumple", each if _ = "" then null else Number.FromText(_, "en-US"), type number}
    })
in
    Typed
