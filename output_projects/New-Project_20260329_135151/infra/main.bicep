targetScope = 'subscription'

@description('Which environment (dev/test/prod)?')
@allowed([
  'dev'
  'test'
  'prod'
])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = 'eastus'

@description('Name prefix for all resources')
param namePrefix string = 'aicsm'

var baseName = '${namePrefix}-${environment}'
var tags = {
  Environment: environment
  Project: 'AI-CSM'
  ManagedBy: 'Bicep'
  CreatedDate: utcNow('yyyy-MM-dd')
}

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'rg-${baseName}'
  location: location
  tags: tags
}

// Deploy modules
module kv 'modules/keyvault.bicep' = {
  name: 'deploy-keyvault'
  scope: rg
  params: {
    baseName: baseName
    location: location
    tags: tags
  }
}

module db 'modules/db.bicep' = {
  name: 'deploy-db'
  scope: rg
  params: {
    baseName: baseName
    location: location
    tags: tags
  }
}

module st 'modules/storage.bicep' = {
  name: 'deploy-storage'
  scope: rg
  params: {
    baseName: baseName
    location: location
    tags: tags
  }
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'deploy-monitoring'
  scope: rg
  params: {
    baseName: baseName
    location: location
    tags: tags
  }
}

module api 'modules/api.bicep' = {
  name: 'deploy-api'
  scope: rg
  params: {
    baseName: baseName
    location: location
    tags: tags
    keyVaultName: kv.outputs.keyVaultName
    sqlConnectionString: db.outputs.connectionString
    storageAccountName: st.outputs.storageAccountName
    logAnalyticsId: monitoring.outputs.logAnalyticsId
    appInsightsKey: monitoring.outputs.instrumentationKey
  }
}

module web 'modules/web.bicep' = {
  name: 'deploy-web'
  scope: rg
  params: {
    baseName: baseName
    location: location
    tags: tags
    storageAccountName: st.outputs.storageAccountName
  }
}

module cdn 'modules/cdn.bicep' = {
  name: 'deploy-cdn'
  scope: rg
  params: {
    baseName: baseName
    location: location
    tags: tags
    webAppEndpoint: web.outputs.webAppEndpoint
  }
}

module frontdoor 'modules/frontdoor.bicep' = {
  name: 'deploy-frontdoor'
  scope: rg
  params: {
    baseName: baseName
    location: location
    tags: tags
    apiEndpoint: api.outputs.apiFqdn
    webEndpoint: cdn.outputs.cdnEndpoint
  }
}

output apiEndpoint string = 'https://${api.outputs.apiFqdn}'
output webEndpoint string = 'https://${frontdoor.outputs.frontDoorFqdn}'