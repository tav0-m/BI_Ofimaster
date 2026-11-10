let
    Source = Csv.Document(File.Contents(pRutaModelo & "FactRepartos.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumns(Headers, {
        {"FechaCorte", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"FechaPromesa", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"FechaPromesaEstadistica", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"CantidadProgramada", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"CantidadRecibidaAcumulada", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"CantidadPendienteAbierta", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"ValorPendienteMonedaOC", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"VencidoAlCorte", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"DiasAtraso", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"Elegible", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"OTIFEvaluable", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"OTIFCumple", each if _ = "" then null else Number.FromText(_, "en-US"), type number}
    })
in
    Typed
