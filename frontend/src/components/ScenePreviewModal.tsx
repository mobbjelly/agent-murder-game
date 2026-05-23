import { assetUrl, GameView } from '../api'

export function ScenePreviewModal({
  scene,
  onClose,
}: {
  scene: GameView['scene_images'][number]
  onClose: () => void
}) {
  return (
    <div className="image-preview-backdrop" onClick={onClose}>
      <section
        className="image-preview-modal"
        onClick={(event) => event.stopPropagation()}
      >
        <button className="close-button" onClick={onClose}>
          ×
        </button>
        <img src={assetUrl(scene.image_url)} alt={scene.name} />
      </section>
    </div>
  )
}
