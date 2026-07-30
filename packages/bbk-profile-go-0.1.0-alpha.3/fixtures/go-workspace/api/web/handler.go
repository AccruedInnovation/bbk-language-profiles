package web

import (
	"html/template"
	"net/http"
)

const fixtureFragment = `<section id="result" hx-target="#result" x-data="{open:true}">{{.}}</section>`

func Handler() http.Handler {
	parsed := template.Must(template.New("fragment").Parse(fixtureFragment))
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = parsed.Execute(w, r.URL.Path)
	})
}
