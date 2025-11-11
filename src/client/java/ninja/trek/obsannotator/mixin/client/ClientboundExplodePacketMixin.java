package ninja.trek.obsannotator.mixin.client;

import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.network.protocol.game.ClientboundExplodePacket;
import net.minecraft.util.random.WeightedList;
import net.minecraft.world.phys.Vec3;
import ninja.trek.obsannotator.events.ExplosionEventHandler;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.Optional;

@Mixin(ClientboundExplodePacket.class)
public class ClientboundExplodePacketMixin {

    @Inject(method = "<init>(Lnet/minecraft/world/phys/Vec3;FILjava/util/Optional;Lnet/minecraft/core/particles/ParticleOptions;Lnet/minecraft/core/Holder;Lnet/minecraft/util/random/WeightedList;)V",
            at = @At("RETURN"))
    private void onExplosion(Vec3 position, float power, int interaction, Optional<?> affectedBlocks,
                            ParticleOptions smallExplosionParticles, Holder<?> explosionSound,
                            WeightedList<?> largeExplosionParticles, CallbackInfo ci) {
        ExplosionEventHandler.onExplosion(position.x, position.y, position.z);
    }
}
