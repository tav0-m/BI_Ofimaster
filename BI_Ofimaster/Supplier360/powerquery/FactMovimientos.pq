let
    Source = Csv.Document(File.Contents(pRutaModelo & "FactMovimientos.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumns(Headers, {
        {"FechaContable", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"FechaDocumento", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"Entrada", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"Salida", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"CantidadNetaBase", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"ImporteOrigen", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"FechaExtraccion", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date}
    })
in
    Typed
