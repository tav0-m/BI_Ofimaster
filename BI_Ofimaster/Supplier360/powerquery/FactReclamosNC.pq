let
    Source = Csv.Document(File.Contents(pRutaModelo & "FactReclamosNC.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumns(Headers, {
        {"FilaOrigen", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"FechaCaso", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"MontoReclamado", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"ContabilizadaVerificada", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"FechaContabilizacion", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"MontoNCContable", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"SaldoNCContable", each if _ = "" then null else Number.FromText(_, "en-US"), type number}
    })
in
    Typed
