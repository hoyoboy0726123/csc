param location string = resourceGroup().location
param environment string
param appName string = 'ai-csm-web'
param storageModuleName string = 'storage'
param cdnModuleName string = 'cdn'

module stg 'storage.bicep' = {
  name: '${storageModuleName}-deployment'
  params: {
    location: location
    environment: environment
  }
}

module cdn 'cdn.bicep' = {
  name: '${cdnModuleName}-deployment'
  params: {
    location: location
    environment: environment
    storageId: stg.outputs.storageId
    storageEndpoint: stg.outputs.blobEndpoint
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: 'asp-${appName}-${environment}'
  location: location
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  kind: 'app'
}

resource webApp 'Microsoft.Web/sites@2022-09-01' = {
  name: '${appName}-${environment}'
  location: location
  kind: 'app'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      alwaysOn: true
      http20Enabled: true
      minTlsVersion: '1.3'
      ftpsState: 'Disabled'
      appSettings: [
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'ENVIRONMENT'
          value: environment
        }
        {
          name: 'BLOB_ENDPOINT'
          value: stg.outputs.blobEndpoint
        }
        {
          name: 'CDN_ENDPOINT'
          value: cdn.outputs.endpoint
        }
      ]
      cors: {
        allowedOrigins: [
          cdn.outputs.endpoint
        ]
      }
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

output webAppId string = webApp.id
output webAppEndpoint string = 'https://${webApp.properties.defaultHostName}'
output cdnEndpoint string = cdn.outputs.endpoint