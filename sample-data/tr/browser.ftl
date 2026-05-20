# Sample Turkish translation with intentional issues so the scripts
# have something to flag. From top to bottom:
#  - bookmarks-count: missing the $count placeable in the [one] branch (placeable bug)
#  - welcome-banner: missing $name (placeable bug)
#  - settings-saved: entry exists but the value is empty (empty bug)
#  - missing entirely: nothing here for new-tab-button's .tooltiptext

-brand-short-name = Firefox

new-tab-button =
    .label = Yeni sekme

bookmarks-count =
    { $count ->
        [one] Bir yer iminiz var
       *[other] { $count } yer iminiz var
    }

welcome-banner = { -brand-short-name } uygulamasına hoş geldiniz!

settings-saved =
