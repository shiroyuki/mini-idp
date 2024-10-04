export async function loadRealm({ params }: { params: any }) {
  return {
    realmId: params.realmId,
  }
}