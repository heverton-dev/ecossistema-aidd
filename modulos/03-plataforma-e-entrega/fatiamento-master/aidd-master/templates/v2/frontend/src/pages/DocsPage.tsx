import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BookOpen, ExternalLink, Code2, Webhook, Bot } from 'lucide-react'

export default function DocsPage() {
  const links = [
    { title: 'OpenAPI / Swagger Studio', desc: 'Contratos e documentação interativa da API REST', url: '/docs', icon: Code2 },
    { title: 'Webhook Studio', desc: 'Gerenciador e endpoints de disparo de eventos', url: '/webhooks', icon: Webhook },
    { title: 'MCP Studio', desc: 'Servidor Model Context Protocol exposto para IA', url: '/mcp', icon: Bot },
    { title: 'Guia do Utilizador', desc: 'Documentação viva e manuais de utilização', url: '/docs/guia', icon: BookOpen },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Documentação & Quarteto Sine Qua Non</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {links.map((item) => (
          <Card key={item.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-base font-semibold">{item.title}</CardTitle>
              <item.icon className="h-5 w-5 text-primary" />
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">{item.desc}</p>
              <a
                href={item.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-primary hover:underline font-medium"
              >
                Abrir estúdio <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
