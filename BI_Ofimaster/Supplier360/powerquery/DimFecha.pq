let
    Source = Csv.Document(File.Contents(pRutaModelo & "DimFecha.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumns(Headers, {
        {"Fecha", each if _ = "" then null else Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date},
        {"Anio", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"Mes", each if _ = "" then null else Number.FromText(_, "en-US"), type number},
        {"Trimestre", each if _ = "" then null else Number.FromText(_, "en-US"), type number}
    })
in
    Typed
