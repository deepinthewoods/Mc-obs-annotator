package ninja.trek.obsannotator.mixin.client;

import net.minecraft.network.protocol.game.ClientboundExplodePacket;
import ninja.trek.obsannotator.events.ExplosionEventHandler;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ClientboundExplodePacket.class)
public class ClientboundExplodePacketMixin {

    @Inject(method = "<init>(DDDFLjava/util/List;Lnet/minecraft/world/phys/Vec3;Lnet/minecraft/network/protocol/game/ClientboundExplodePacket$BlockInteraction;Lnet/minecraft/core/particles/ParticleOptions;Lnet/minecraft/core/particles/ParticleOptions;Lnet/minecraft/core/Holder;)V",
            at = @At("RETURN"))
    private void onExplosion(CallbackInfo ci) {
        ClientboundExplodePacket packet = (ClientboundExplodePacket) (Object) this;
        ExplosionEventHandler.onExplosion(packet.getX(), packet.getY(), packet.getZ());
    }
}
